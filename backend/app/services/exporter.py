"""Export service for output_takeoff.json, output_boq.csv, and ZIP submission package."""

import os
import csv
import json
import zipfile
from typing import Dict, Any
from backend.app.models.schemas import TakeoffResult


class TakeoffExporter:
    """Generates structured JSON, CSV BOQ, and submission ZIP package."""

    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def export_to_json(self, result: TakeoffResult, file_path: str = None) -> str:
        """Serialize TakeoffResult to structured output_takeoff.json."""
        if not file_path:
            file_path = os.path.join(self.output_dir, "output_takeoff.json")

        result_dict = result.model_dump(exclude={"cad_entities"})
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)

        return file_path

    def export_to_csv(self, result: TakeoffResult, file_path: str = None) -> str:
        """Export BOQ line items to standard output_boq.csv."""
        if not file_path:
            file_path = os.path.join(self.output_dir, "output_boq.csv")

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Item No", "Description", "Quantity", "Unit", "Estimated Rate (INR)", "Estimated Amount (INR)"])

            for item in result.boq_items:
                writer.writerow([
                    item.item_no,
                    item.description,
                    f"{item.quantity:.2f}",
                    item.unit,
                    f"{item.estimated_rate_inr:.2f}",
                    f"{item.estimated_amount_inr:.2f}",
                ])

            # Add Summary Block in CSV
            writer.writerow([])
            writer.writerow(["---", "SUMMARY & TOTAL METRICS", "---", "---", "---", "---"])
            writer.writerow(["S1", "Total Pile Count", f"{result.total_pile_count}", "Nos", "-", "-"])
            writer.writerow(["S2", "Total RMC Concrete Volume", f"{result.concrete_takeoff.total_volume_m3:.3f}", "m³", "-", "-"])
            writer.writerow(["S3", "Total Steel Reinforcement", f"{result.steel_takeoff.total_steel_mt:.4f}", "MT", "-", "-"])
            writer.writerow(["S4", "Total Estimated Manpower", f"{result.manpower_estimation.total_mandays:.2f}", "Man-Days", "-", "-"])

        return file_path

    def create_submission_zip(
        self,
        base_dir: str,
        zip_name: str = "BuildIQ_Candidate_Assessment.zip",
    ) -> str:
        """Package source code, schemas, output artifacts, requirements, and README into a submission zip."""
        zip_path = os.path.join(self.output_dir, zip_name)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(base_dir):
                # Skip node_modules, __pycache__, .venv, .git
                dirs[:] = [d for d in dirs if d not in ("node_modules", "__pycache__", ".venv", ".git", ".next", "dist")]
                for file in files:
                    if file.endswith((".pyc", ".pyo", ".pyd")):
                        continue
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, base_dir)
                    zipf.write(full_path, rel_path)

        return zip_path


# Global exporter instance
exporter = TakeoffExporter()
