"""Generate sample takeoff artifacts (output_takeoff.json, output_boq.csv)."""

import asyncio
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app.services.extractor import takeoff_pipeline
from backend.app.services.exporter import exporter


async def run_generation():
    dxf_sample = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../sample files/PILE LAYOUT AND DETAILS (27.09.2024) 1.dxf"))
    pdf_sample = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../sample files/PILE LAYOUT AND DETAILS (27.09.2024) 1-area.pdf"))

    print(f"Loading DXF from: {dxf_sample} (exists: {os.path.exists(dxf_sample)})")
    print(f"Loading PDF from: {pdf_sample} (exists: {os.path.exists(pdf_sample)})")

    res = await takeoff_pipeline.process_drawings(
        dxf_path=dxf_sample if os.path.exists(dxf_sample) else None,
        pdf_path=pdf_sample if os.path.exists(pdf_sample) else None,
        project_title="PILE LAYOUT AND DETAILS (27.09.2024)",
    )

    out_root_json = os.path.abspath(os.path.join(os.path.dirname(__file__), "../output_takeoff.json"))
    out_root_csv = os.path.abspath(os.path.join(os.path.dirname(__file__), "../output_boq.csv"))
    out_backend_json = os.path.abspath(os.path.join(os.path.dirname(__file__), "outputs/output_takeoff.json"))
    out_backend_csv = os.path.abspath(os.path.join(os.path.dirname(__file__), "outputs/output_boq.csv"))

    exporter.export_to_json(res, out_root_json)
    exporter.export_to_csv(res, out_root_csv)
    exporter.export_to_json(res, out_backend_json)
    exporter.export_to_csv(res, out_backend_csv)

    print("\n" + "=" * 60)
    print("SUCCESSFULLY GENERATED TAKEOFF ARTIFACTS")
    print("=" * 60)
    print(f"Project Title:            {res.project_title}")
    print(f"Total Pile Count:         {res.total_pile_count} Nos")
    print(f"Total Concrete Volume:    {res.concrete_takeoff.total_volume_m3:.3f} m³")
    print(f"Volume with 5% Wastage:   {res.concrete_takeoff.volume_with_5pct_wastage_m3:.3f} m³")
    print(f"Total Steel Reinforcement:{res.steel_takeoff.total_steel_mt:.4f} MT ({res.steel_takeoff.total_steel_kg:.2f} kg)")
    print(f"Total Labor / Man-Days:   {res.manpower_estimation.total_mandays:.2f} Man-Days")
    print(f" - Piling & Concreting:   {res.manpower_estimation.piling_and_concreting_mandays:.2f} Man-Days")
    print(f" - Rebar Fabrication:     {res.manpower_estimation.rebar_fabrication_mandays:.2f} Man-Days")
    print(f" - Pile Head Chipping:    {res.manpower_estimation.pile_head_chipping_mandays:.2f} Man-Days")
    print(f"\nArtifacts written to:")
    print(f" - {out_root_json}")
    print(f" - {out_root_csv}")


if __name__ == "__main__":
    asyncio.run(run_generation())
