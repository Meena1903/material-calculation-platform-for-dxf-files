"""PDF Blueprint Rendering and High-Definition (HD) Region-of-Interest (ROI) Cropper."""

import os
import base64
from typing import List, Dict, Any, Optional, Tuple
import pymupdf  # PyMuPDF
from backend.app.core.logging_config import pdf_logger


class PDFVisionParser:
    """Renders PDF blueprints and creates high-resolution crops for vision models."""

    def __init__(self, output_dir: str = "outputs/crops"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        pdf_logger.info(f"[PDF INIT] Initialized PDFVisionParser with output_dir='{self.output_dir}'")

    def render_pdf_to_images(self, pdf_path: str, dpi: int = 200) -> List[str]:
        """Render all pages of a PDF drawing to high-res PNG images."""
        pdf_logger.info(f"[PDF STEP 1: RENDER ALL] Opening PDF '{pdf_path}' at DPI={dpi}")
        if not os.path.exists(pdf_path):
            pdf_logger.error(f"[PDF STEP 1: NOT FOUND] PDF file not found at: '{pdf_path}'")
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        rendered_paths: List[str] = []
        doc = pymupdf.open(pdf_path)
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        pdf_logger.info(f"[PDF STEP 2: PAGES DETECTED] Document '{base_name}' has {len(doc)} pages")

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            zoom = dpi / 72.0
            mat = pymupdf.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            img_filename = f"{base_name}_page_{page_idx + 1}.png"
            img_path = os.path.join(self.output_dir, img_filename)
            pix.save(img_path)
            rendered_paths.append(img_path)
            pdf_logger.info(f"[PDF STEP 3: PAGE SAVED] Page {page_idx + 1}/{len(doc)} saved to '{img_path}' (size: {pix.width}x{pix.height}px)")

        doc.close()
        return rendered_paths

    def extract_hd_crops(self, pdf_path: str, dpi: int = 300) -> Dict[str, str]:
        """Extract specialized high-resolution crops targeting key engineering regions:
        1. Schedule Table Region (typically right-hand quadrant)
        2. Cross-Section Reinforcement Details (typically lower-left or central bottom)
        3. Title Block and General Notes
        """
        pdf_logger.info("=" * 80)
        pdf_logger.info(f"[PDF STEP 4: HD CROPS START] Extracting HD ROI crops from '{pdf_path}' at DPI={dpi}")
        pdf_logger.info("=" * 80)

        if not os.path.exists(pdf_path):
            pdf_logger.error(f"[PDF STEP 4: NOT FOUND] PDF file not found at: '{pdf_path}'")
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        doc = pymupdf.open(pdf_path)
        page = doc[0]  # First sheet
        rect = page.rect  # width, height
        pdf_logger.info(f"[PDF STEP 4a: SHEET GEOMETRY] Page 1 rect: width={rect.width:.1f}pt, height={rect.height:.1f}pt")

        zoom = dpi / 72.0
        mat = pymupdf.Matrix(zoom, zoom)

        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        crop_paths: Dict[str, str] = {}

        # 1. Schedule Table Crop (Right 45% of the sheet)
        sched_rect = pymupdf.Rect(rect.width * 0.55, rect.height * 0.05, rect.width * 0.98, rect.height * 0.95)
        pix_sched = page.get_pixmap(matrix=mat, clip=sched_rect, alpha=False)
        sched_path = os.path.join(self.output_dir, f"{base_name}_crop_schedule.png")
        pix_sched.save(sched_path)
        crop_paths["schedule_table"] = sched_path
        pdf_logger.info(
            f"[PDF STEP 4b: SCHEDULE TABLE CROP] Saved schedule crop to '{sched_path}' "
            f"({pix_sched.width}x{pix_sched.height}px, clip: x={sched_rect.x0:.0f}..{sched_rect.x1:.0f}, y={sched_rect.y0:.0f}..{sched_rect.y1:.0f})"
        )

        # 2. Rebar Cross-Section Detail Crop (Lower 45% section)
        rebar_rect = pymupdf.Rect(rect.width * 0.02, rect.height * 0.55, rect.width * 0.60, rect.height * 0.98)
        pix_rebar = page.get_pixmap(matrix=mat, clip=rebar_rect, alpha=False)
        rebar_path = os.path.join(self.output_dir, f"{base_name}_crop_sections.png")
        pix_rebar.save(rebar_path)
        crop_paths["rebar_sections"] = rebar_path
        pdf_logger.info(
            f"[PDF STEP 4c: REBAR SECTIONS CROP] Saved rebar sections crop to '{rebar_path}' "
            f"({pix_rebar.width}x{pix_rebar.height}px, clip: x={rebar_rect.x0:.0f}..{rebar_rect.x1:.0f}, y={rebar_rect.y0:.0f}..{rebar_rect.y1:.0f})"
        )

        # 3. Overall Full Page Overview (Lower DPI for context)
        overview_mat = pymupdf.Matrix(100 / 72.0, 100 / 72.0)
        pix_overview = page.get_pixmap(matrix=overview_mat, alpha=False)
        overview_path = os.path.join(self.output_dir, f"{base_name}_overview.png")
        pix_overview.save(overview_path)
        crop_paths["overview"] = overview_path
        pdf_logger.info(f"[PDF STEP 4d: OVERVIEW CROP] Saved overview image to '{overview_path}' ({pix_overview.width}x{pix_overview.height}px)")

        doc.close()
        pdf_logger.info(f"[PDF STEP 4e: CROPS COMPLETE] Generated {len(crop_paths)} ROI crops successfully.")
        return crop_paths

    def encode_image_to_base64(self, image_path: str) -> str:
        """Encode image file to base64 string for NVIDIA NIM API payloads."""
        if not os.path.exists(image_path):
            pdf_logger.error(f"[PDF STEP 5: FILE NOT FOUND] Image file not found: '{image_path}'")
            raise FileNotFoundError(f"Image not found: {image_path}")

        file_size_kb = round(os.path.getsize(image_path) / 1024, 2)
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")
        
        pdf_logger.info(f"[PDF STEP 5: BASE64 ENCODE] Encoded '{image_path}' ({file_size_kb} KB) -> Base64 Length: {len(encoded)} chars")
        return encoded


# Global PDF parser instance
pdf_vision_parser = PDFVisionParser()
