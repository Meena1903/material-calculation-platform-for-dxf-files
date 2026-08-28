"""FastAPI API Endpoints for Takeoff Engine."""

import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from backend.app.core.config import settings
from backend.app.core.logging_config import api_logger
from backend.app.models.schemas import TakeoffResult
from backend.app.services.extractor import takeoff_pipeline
from backend.app.services.calculator import calculator
from backend.app.services.exporter import exporter
from backend.app.services.nvidia_nim_extractor import nim_vision_client
from backend.app.services.dxf_parser import dxf_parser

router = APIRouter(prefix="/api", tags=["Takeoff Engine"])


class RecalculateRequest(BaseModel):
    pile_specs: List[dict]
    project_title: Optional[str] = "Custom Takeoff Calculation"


@router.get("/health")
async def health_check():
    """Health check endpoint and NVIDIA NIM API connectivity status."""
    api_logger.info("[API GET /api/health] Received health check request")
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


@router.get("/takeoff/sample", response_model=TakeoffResult)
async def get_sample_takeoff():
    """Load verified sample foundation takeoff for 'PILE LAYOUT AND DETAILS'."""
    api_logger.info("=" * 80)
    api_logger.info("[API GET /api/takeoff/sample] Request received for sample foundation takeoff")
    api_logger.info("=" * 80)

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


@router.post("/takeoff/upload", response_model=TakeoffResult)
async def upload_and_process_drawings(
    dxf_file: Optional[UploadFile] = File(None),
    pdf_file: Optional[UploadFile] = File(None),
    project_title: Optional[str] = Form("Uploaded Foundation Takeoff"),
):
    """Upload CAD DXF and/or PDF drawings, run visual & geometry parsing, and calculate takeoff."""
    api_logger.info("=" * 80)
    api_logger.info(
        f"[API POST /api/takeoff/upload] Upload received: "
        f"dxf={getattr(dxf_file, 'filename', None)}, pdf={getattr(pdf_file, 'filename', None)}, title='{project_title}'"
    )
    api_logger.info("=" * 80)

    if not dxf_file and not pdf_file:
        api_logger.warning("[API UPLOAD ERROR] No files provided in upload request")
        raise HTTPException(status_code=400, detail="At least one drawing file (DXF or PDF) must be provided.")

    saved_dxf_path = None
    saved_pdf_path = None

    if dxf_file:
        saved_dxf_path = os.path.join(settings.UPLOAD_DIR, dxf_file.filename)
        api_logger.info(f"[API STEP 1: SAVE DXF] Saving uploaded DXF to '{saved_dxf_path}'")
        with open(saved_dxf_path, "wb") as buffer:
            shutil.copyfileobj(dxf_file.file, buffer)

    if pdf_file:
        saved_pdf_path = os.path.join(settings.UPLOAD_DIR, pdf_file.filename)
        api_logger.info(f"[API STEP 2: SAVE PDF] Saving uploaded PDF to '{saved_pdf_path}'")
        with open(saved_pdf_path, "wb") as buffer:
            shutil.copyfileobj(pdf_file.file, buffer)

    api_logger.info(f"[API STEP 3: RUN PIPELINE] Processing uploaded drawings...")
    result = await takeoff_pipeline.process_drawings(
        dxf_path=saved_dxf_path,
        pdf_path=saved_pdf_path,
        project_title=project_title,
    )

    # Save output artifacts
    api_logger.info(f"[API STEP 4: EXPORT] Saving output artifacts...")
    exporter.export_to_json(result)
    exporter.export_to_csv(result)

    api_logger.info(f"[API POST /api/takeoff/upload: SUCCESS] Finished upload processing for '{project_title}'")
    return result


@router.post("/takeoff/calculate", response_model=TakeoffResult)
async def recalculate_takeoff(request: RecalculateRequest):
    """Recalculate quantities with custom pile overrides in 100% native Python."""
    api_logger.info(
        f"[API POST /api/takeoff/calculate] Recalculation requested for '{request.project_title}' "
        f"with {len(request.pile_specs)} pile specs"
    )
    result = calculator.calculate_full_takeoff(
        raw_pile_specs=request.pile_specs,
        project_title=request.project_title,
    )
    exporter.export_to_json(result)
    exporter.export_to_csv(result)
    api_logger.info(f"[API POST /api/takeoff/calculate: SUCCESS] Recalculation complete")
    return result


@router.get("/export/json")
async def download_output_json():
    """Download output_takeoff.json."""
    json_path = os.path.join(settings.OUTPUT_DIR, "output_takeoff.json")
    api_logger.info(f"[API GET /api/export/json] Download requested for '{json_path}'")
    if not os.path.exists(json_path):
        api_logger.info("[API EXPORT JSON] File not found, generating sample takeoff...")
        sample_result = await get_sample_takeoff()
        exporter.export_to_json(sample_result, json_path)

    return FileResponse(
        path=json_path,
        filename="output_takeoff.json",
        media_type="application/json",
    )


@router.get("/export/csv")
async def download_output_csv():
    """Download output_boq.csv."""
    csv_path = os.path.join(settings.OUTPUT_DIR, "output_boq.csv")
    api_logger.info(f"[API GET /api/export/csv] Download requested for '{csv_path}'")
    if not os.path.exists(csv_path):
        api_logger.info("[API EXPORT CSV] File not found, generating sample takeoff...")
        sample_result = await get_sample_takeoff()
        exporter.export_to_csv(sample_result, csv_path)

    return FileResponse(
        path=csv_path,
        filename="output_boq.csv",
        media_type="text/csv",
    )


@router.get("/export/zip")
async def download_submission_zip():
    """Download candidate submission zip package."""
    api_logger.info("[API GET /api/export/zip] Packaging submission zip...")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    zip_path = exporter.create_submission_zip(base_dir=base_dir)

    return FileResponse(
        path=zip_path,
        filename="BuildIQ_Candidate_Assessment.zip",
        media_type="application/zip",
    )
