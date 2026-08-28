"""Generate sample takeoff artifacts (output_takeoff.json, output_boq.csv)."""

import asyncio
import os
import sys

# Ensure repository root is in sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from backend.app.core.logging_config import app_logger
from backend.app.services.extractor import takeoff_pipeline
from backend.app.services.exporter import exporter


async def run_generation():
    app_logger.info("=" * 80)
    app_logger.info("[ARTIFACT GENERATION STEP 1] Starting Standalone Takeoff Artifact Generation")
    app_logger.info("=" * 80)

    dxf_sample = os.path.abspath(os.path.join(repo_root, "sample files/PILE LAYOUT AND DETAILS (27.09.2024) 1.dxf"))
    pdf_sample = os.path.abspath(os.path.join(repo_root, "sample files/PILE LAYOUT AND DETAILS (27.09.2024) 1-area.pdf"))

    app_logger.info(f"[ARTIFACT GENERATION STEP 2] Sample DXF Path: {dxf_sample} (exists: {os.path.exists(dxf_sample)})")
    app_logger.info(f"[ARTIFACT GENERATION STEP 2] Sample PDF Path: {pdf_sample} (exists: {os.path.exists(pdf_sample)})")

    app_logger.info("[ARTIFACT GENERATION STEP 3] Executing Takeoff Pipeline...")
    res = await takeoff_pipeline.process_drawings(
        dxf_path=dxf_sample if os.path.exists(dxf_sample) else None,
        pdf_path=pdf_sample if os.path.exists(pdf_sample) else None,
        project_title="PILE LAYOUT AND DETAILS (27.09.2024)",
    )

    out_root_json = os.path.abspath(os.path.join(repo_root, "output_takeoff.json"))
    out_root_csv = os.path.abspath(os.path.join(repo_root, "output_boq.csv"))
    out_backend_json = os.path.abspath(os.path.join(os.path.dirname(__file__), "outputs/output_takeoff.json"))
    out_backend_csv = os.path.abspath(os.path.join(os.path.dirname(__file__), "outputs/output_boq.csv"))

    app_logger.info("[ARTIFACT GENERATION STEP 4] Exporting to output artifacts (Root + Backend)...")
    exporter.export_to_json(res, out_root_json)
    exporter.export_to_csv(res, out_root_csv)
    exporter.export_to_json(res, out_backend_json)
    exporter.export_to_csv(res, out_backend_csv)

    app_logger.info("=" * 80)
    app_logger.info("[ARTIFACT GENERATION STEP 5] SUMMARY OF GENERATED TAKEOFF ARTIFACTS")
    app_logger.info("=" * 80)
    app_logger.info(f"Project Title:             {res.project_title}")
    app_logger.info(f"Total Pile Count:          {res.total_pile_count} Nos")
    app_logger.info(f"Total Concrete Volume:     {res.concrete_takeoff.total_volume_m3:.3f} m³")
    app_logger.info(f"Volume with 5% Wastage:    {res.concrete_takeoff.volume_with_5pct_wastage_m3:.3f} m³")
    app_logger.info(f"Total Steel Reinforcement: {res.steel_takeoff.total_steel_mt:.4f} MT ({res.steel_takeoff.total_steel_kg:.2f} kg)")
    app_logger.info(f"Total Labor / Man-Days:    {res.manpower_estimation.total_mandays:.2f} Man-Days")
    app_logger.info(f"  - Piling & Concreting:   {res.manpower_estimation.piling_and_concreting_mandays:.2f} Man-Days")
    app_logger.info(f"  - Rebar Fabrication:     {res.manpower_estimation.rebar_fabrication_mandays:.2f} Man-Days")
    app_logger.info(f"  - Pile Head Chipping:    {res.manpower_estimation.pile_head_chipping_mandays:.2f} Man-Days")
    app_logger.info("Artifacts written to:")
    app_logger.info(f"  - {out_root_json}")
    app_logger.info(f"  - {out_root_csv}")
    app_logger.info("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_generation())
