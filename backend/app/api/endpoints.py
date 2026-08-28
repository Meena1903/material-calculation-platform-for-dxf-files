"""FastAPI API Endpoints for Takeoff Engine."""

import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from backend.app.core.logging_config import api_logger
from backend.app.models.schemas import TakeoffResult
from backend.app.services.extractor import takeoff_pipeline
from backend.app.services.calculator import calculator
from backend.app.services.exporter import exporter
from backend.app.services.nvidia_nim_extractor import nim_vision_client
from backend.app.services.dxf_parser import dxf_parser

router = APIRouter(prefix="/api", tags=["Takeoff Engine"])

# Supported file extensions
ALLOWED_EXTENSIONS = {".dxf", ".dwg", ".pdf"}
HTTP_413 = getattr(status, "HTTP_413_CONTENT_TOO_LARGE", getattr(status, "HTTP_413_REQUEST_ENTITY_TOO_LARGE", 413))


class RecalculateRequest(BaseModel):
    pile_specs: List[dict] = Field(default_factory=list, description="Array of pile specification dictionaries")
    project_title: Optional[str] = Field(default="Custom Takeoff Calculation", description="Project title")


@router.get("/health")
async def health_check():
    """Health check endpoint and NVIDIA NIM API connectivity status with error handling."""
    api_logger.info("[API GET /api/health] Received health check request")
    try:
        nim_status = await nim_vision_client.check_health()
        resp = {
            "status": "healthy",
            "app_name": settings.APP_NAME,
            "environment": settings.APP_ENV,
            "nvidia_nim": nim_status,
            "calculation_engine": "Native Python 3.14 (IS 1786 / SP 34 deterministic)",
        }
        api_logger.info(f"[API GET /api/health: RESPONSE] App healthy | NIM Status: {nim_status['status']}")
        return resp
    except Exception as e:
        api_logger.error(f"[API HEALTH ERROR] Health check encountered exception: {e}")
        return {
            "status": "degraded",
            "app_name": settings.APP_NAME,
            "error": str(e),
            "calculation_engine": "Native Python 3.14 (IS 1786 / SP 34 deterministic)",
        }


@router.get("/takeoff/sample", response_model=TakeoffResult)
async def get_sample_takeoff():
    """Load verified sample foundation takeoff for 'PILE LAYOUT AND DETAILS'."""
    api_logger.info("=" * 80)
    api_logger.info("[API GET /api/takeoff/sample] Request received for sample foundation takeoff")
    api_logger.info("=" * 80)

    try:
        # Check if sample files exist in workspace
        sample_dxf = "sample files/PILE LAYOUT AND DETAILS (27.09.2024) 1.dxf"
        sample_pdf = "sample files/PILE LAYOUT AND DETAILS (27.09.2024) 1-area.pdf"

        dxf_target = sample_dxf if os.path.exists(sample_dxf) else None
        pdf_target = sample_pdf if os.path.exists(sample_pdf) else None

        api_logger.info(f"[API STEP 1: RESOLVE SAMPLE FILES] DXF: {dxf_target} | PDF: {pdf_target}")

        result = await takeoff_pipeline.process_drawings(
            dxf_path=dxf_target,
            pdf_path=pdf_target,
            project_title="PILE LAYOUT AND DETAILS (27.09.2024)",
        )

        # Save output artifacts
        api_logger.info("[API STEP 2: EXPORT ARTIFACTS] Exporting sample takeoff to JSON and CSV")
        exporter.export_to_json(result)
        exporter.export_to_csv(result)

        api_logger.info(f"[API GET /api/takeoff/sample: SUCCESS] Returning takeoff for {result.total_pile_count} piles")
        return result
    except Exception as e:
        api_logger.error(f"[API SAMPLE TAKEOFF EXCEPTION] Error loading sample takeoff: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate sample takeoff: {str(e)}",
        )


@router.post("/takeoff/upload", response_model=TakeoffResult)
async def upload_and_process_drawings(
    dxf_file: Optional[UploadFile] = File(None),
    pdf_file: Optional[UploadFile] = File(None),
    project_title: Optional[str] = Form("Uploaded Foundation Takeoff"),
):
    """Upload CAD DXF and/or PDF drawings, run visual & geometry parsing, and calculate takeoff with strict validation."""
    api_logger.info("=" * 80)
    api_logger.info(
        f"[API POST /api/takeoff/upload] Upload received: "
        f"dxf={getattr(dxf_file, 'filename', None)}, pdf={getattr(pdf_file, 'filename', None)}, title='{project_title}'"
    )
    api_logger.info("=" * 80)

    if not dxf_file and not pdf_file:
        api_logger.warning("[API UPLOAD ERROR] No files provided in upload request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one drawing file (DXF or PDF) must be provided for takeoff analysis.",
        )

    # Validate file extensions
    for upload in (dxf_file, pdf_file):
        if upload and upload.filename:
            ext = os.path.splitext(upload.filename)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                api_logger.warning(f"[API UPLOAD ERROR] Invalid file extension '{ext}' in '{upload.filename}'")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file format '{ext}' in '{upload.filename}'. Allowed extensions: {list(ALLOWED_EXTENSIONS)}",
                )

    saved_dxf_path = None
    saved_pdf_path = None

    try:
        max_size = settings.MAX_UPLOAD_SIZE_BYTES
        max_size_mb = int(max_size / (1024 * 1024))

        if dxf_file and dxf_file.filename:
            safe_dxf_name = os.path.basename(dxf_file.filename)
            saved_dxf_path = os.path.join(settings.UPLOAD_DIR, safe_dxf_name)
            api_logger.info(f"[API STEP 1: SAVE DXF] Saving uploaded DXF to '{saved_dxf_path}'")
            with open(saved_dxf_path, "wb") as buffer:
                shutil.copyfileobj(dxf_file.file, buffer)

            # Check file size against configured limit
            dxf_size = os.path.getsize(saved_dxf_path)
            if dxf_size > max_size:
                os.remove(saved_dxf_path)
                raise HTTPException(
                    status_code=HTTP_413,
                    detail=f"Uploaded DXF file '{safe_dxf_name}' ({dxf_size / (1024*1024):.1f} MB) exceeds {max_size_mb}MB size limit.",
                )

        if pdf_file and pdf_file.filename:
            safe_pdf_name = os.path.basename(pdf_file.filename)
            saved_pdf_path = os.path.join(settings.UPLOAD_DIR, safe_pdf_name)
            api_logger.info(f"[API STEP 2: SAVE PDF] Saving uploaded PDF to '{saved_pdf_path}'")
            with open(saved_pdf_path, "wb") as buffer:
                shutil.copyfileobj(pdf_file.file, buffer)

            # Check file size against configured limit
            pdf_size = os.path.getsize(saved_pdf_path)
            if pdf_size > max_size:
                os.remove(saved_pdf_path)
                raise HTTPException(
                    status_code=HTTP_413,
                    detail=f"Uploaded PDF file '{safe_pdf_name}' ({pdf_size / (1024*1024):.1f} MB) exceeds {max_size_mb}MB size limit.",
                )

        api_logger.info(f"[API STEP 3: RUN PIPELINE] Processing uploaded drawings...")
        result = await takeoff_pipeline.process_drawings(
            dxf_path=saved_dxf_path,
            pdf_path=saved_pdf_path,
            project_title=project_title or "Uploaded Foundation Takeoff",
        )

        # Save output artifacts
        api_logger.info(f"[API STEP 4: EXPORT] Saving output artifacts...")
        exporter.export_to_json(result)
        exporter.export_to_csv(result)

        api_logger.info(f"[API POST /api/takeoff/upload: SUCCESS] Finished upload processing for '{project_title}'")
        return result
    except HTTPException:
        raise
    except Exception as e:
        api_logger.error(f"[API UPLOAD EXCEPTION] Failed processing uploaded drawings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error processing drawings: {str(e)}",
        )


@router.post("/takeoff/calculate", response_model=TakeoffResult)
async def recalculate_takeoff(request: RecalculateRequest):
    """Recalculate quantities with custom pile overrides in 100% native Python with validation."""
    api_logger.info(
        f"[API POST /api/takeoff/calculate] Recalculation requested for '{request.project_title}' "
        f"with {len(request.pile_specs)} pile specs"
    )
    try:
        result = calculator.calculate_full_takeoff(
            raw_pile_specs=request.pile_specs,
            project_title=request.project_title or "Custom Takeoff Calculation",
        )
        exporter.export_to_json(result)
        exporter.export_to_csv(result)
        api_logger.info(f"[API POST /api/takeoff/calculate: SUCCESS] Recalculation complete")
        return result
    except Exception as e:
        api_logger.error(f"[API RECALCULATE EXCEPTION] Recalculation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recalculation error: {str(e)}",
        )


@router.get("/export/json")
async def download_output_json():
    """Download output_takeoff.json with error handling."""
    json_path = os.path.join(settings.OUTPUT_DIR, "output_takeoff.json")
    api_logger.info(f"[API GET /api/export/json] Download requested for '{json_path}'")
    try:
        if not os.path.exists(json_path):
            api_logger.info("[API EXPORT JSON] File not found, generating sample takeoff...")
            sample_result = await get_sample_takeoff()
            exporter.export_to_json(sample_result, json_path)

        return FileResponse(
            path=json_path,
            filename="output_takeoff.json",
            media_type="application/json",
        )
    except Exception as e:
        api_logger.error(f"[API EXPORT JSON ERROR] {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to download JSON artifact.")


@router.get("/export/csv")
async def download_output_csv():
    """Download output_boq.csv with error handling."""
    csv_path = os.path.join(settings.OUTPUT_DIR, "output_boq.csv")
    api_logger.info(f"[API GET /api/export/csv] Download requested for '{csv_path}'")
    try:
        if not os.path.exists(csv_path):
            api_logger.info("[API EXPORT CSV] File not found, generating sample takeoff...")
            sample_result = await get_sample_takeoff()
            exporter.export_to_csv(sample_result, csv_path)

        return FileResponse(
            path=csv_path,
            filename="output_boq.csv",
            media_type="text/csv",
        )
    except Exception as e:
        api_logger.error(f"[API EXPORT CSV ERROR] {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to download CSV artifact.")


@router.get("/export/zip")
async def download_submission_zip():
    """Download candidate submission zip package with error handling."""
    api_logger.info("[API GET /api/export/zip] Packaging submission zip...")
    try:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
        zip_path = exporter.create_submission_zip(base_dir=base_dir)

        return FileResponse(
            path=zip_path,
            filename="BuildIQ_Candidate_Assessment.zip",
            media_type="application/zip",
        )
    except Exception as e:
        api_logger.error(f"[API EXPORT ZIP ERROR] {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create submission zip archive.")
