"""PDF Blueprint Rendering and High-Definition (HD) Region-of-Interest (ROI) Cropper."""

import os
import base64
from typing import List, Dict, Any, Optional, Tuple
import pymupdf  # PyMuPDF


class PDFVisionParser:
    """Renders PDF blueprints and creates high-resolution crops for vision models."""

    def __init__(self, output_dir: str = "outputs/crops"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def render_pdf_to_images(self, pdf_path: str, dpi: int = 200) -> List[str]:
        """Render all pages of a PDF drawing to high-res PNG images."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        rendered_paths: List[str] = []
        doc = pymupdf.open(pdf_path)
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            # Zoom matrix for high-res crisp engineering drawings
            zoom = dpi / 72.0
            mat = pymupdf.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            img_filename = f"{base_name}_page_{page_idx + 1}.png"
            img_path = os.path.join(self.output_dir, img_filename)
            pix.save(img_path)
            rendered_paths.append(img_path)

        doc.close()
        return rendered_paths

    def extract_hd_crops(self, pdf_path: str, dpi: int = 300) -> Dict[str, str]:
        """Extract specialized high-resolution crops targeting key engineering regions:
        1. Schedule Table Region (typically right-hand quadrant)
        2. Cross-Section Reinforcement Details (typically lower-left or central bottom)
        3. Title Block and General Notes
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        doc = pymupdf.open(pdf_path)
        page = doc[0]  # First sheet
        rect = page.rect  # width, height

        zoom = dpi / 72.0
        mat = pymupdf.Matrix(zoom, zoom)

        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        crop_paths: Dict[str, str] = {}

        # 1. Schedule Table Crop (Right 40% of the sheet)
        # Rect(x0, y0, x1, y1)
        sched_rect = pymupdf.Rect(rect.width * 0.55, rect.height * 0.05, rect.width * 0.98, rect.height * 0.95)
        pix_sched = page.get_pixmap(matrix=mat, clip=sched_rect, alpha=False)
        sched_path = os.path.join(self.output_dir, f"{base_name}_crop_schedule.png")
        pix_sched.save(sched_path)
        crop_paths["schedule_table"] = sched_path

        # 2. Rebar Cross-Section Detail Crop (Lower 40% section)
        rebar_rect = pymupdf.Rect(rect.width * 0.02, rect.height * 0.55, rect.width * 0.60, rect.height * 0.98)
        pix_rebar = page.get_pixmap(matrix=mat, clip=rebar_rect, alpha=False)
        rebar_path = os.path.join(self.output_dir, f"{base_name}_crop_sections.png")
        pix_rebar.save(rebar_path)
        crop_paths["rebar_sections"] = rebar_path

        # 3. Overall Full Page Overview (Lower DPI for context)
        overview_mat = pymupdf.Matrix(100 / 72.0, 100 / 72.0)
        pix_overview = page.get_pixmap(matrix=overview_mat, alpha=False)
        overview_path = os.path.join(self.output_dir, f"{base_name}_overview.png")
        pix_overview.save(overview_path)
        crop_paths["overview"] = overview_path

        doc.close()
        return crop_paths

    def encode_image_to_base64(self, image_path: str) -> str:
        """Encode image file to base64 string for NVIDIA NIM API payloads."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")


# Global PDF parser instance
pdf_vision_parser = PDFVisionParser()
