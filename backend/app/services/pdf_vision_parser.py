"""PDF Blueprint Rendering and High-Definition (HD) Region-of-Interest (ROI) Cropper."""

import os
import base64
from typing import List, Dict, Any, Optional, Tuple
import pymupdf  # PyMuPDF
from backend.app.core.logging_config import pdf_logger


class PDFVisionParser:
    """Renders PDF blueprints and creates high-resolution crops for vision models with complete error handling."""

    def __init__(self, output_dir: str = "outputs/crops"):
        self.output_dir = output_dir
        try:
            os.makedirs(self.output_dir, exist_ok=True)
        except Exception as e:
            pdf_logger.warning(f"[PDF INIT WARNING] Could not create output directory '{self.output_dir}': {e}")
        pdf_logger.info(f"[PDF INIT] Initialized PDFVisionParser with output_dir='{self.output_dir}'")

    def render_pdf_to_images(self, pdf_path: str, dpi: int = 200) -> List[str]:
        """Render all pages of a PDF drawing to high-res PNG images with error handling."""
        pdf_logger.info(f"[PDF STEP 1: RENDER ALL] Opening PDF '{pdf_path}' at DPI={dpi}")
        if not pdf_path or not os.path.exists(pdf_path):
            pdf_logger.error(f"[PDF STEP 1: NOT FOUND] PDF file not found at: '{pdf_path}'")
            return []

        rendered_paths: List[str] = []
        try:
            doc = pymupdf.open(pdf_path)
            if len(doc) == 0:
                pdf_logger.warning(f"[PDF STEP 2: EMPTY PDF] PDF file has 0 pages: '{pdf_path}'")
                doc.close()
                return []

            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            pdf_logger.info(f"[PDF STEP 2: PAGES DETECTED] Document '{base_name}' has {len(doc)} pages")

            safe_dpi = max(72, min(400, int(dpi))) if dpi else 200
            zoom = safe_dpi / 72.0
            mat = pymupdf.Matrix(zoom, zoom)

            for page_idx in range(len(doc)):
                try:
                    page = doc[page_idx]
                    pix = page.get_pixmap(matrix=mat, alpha=False)

                    img_filename = f"{base_name}_page_{page_idx + 1}.png"
                    img_path = os.path.join(self.output_dir, img_filename)
                    pix.save(img_path)
                    rendered_paths.append(img_path)
                    pdf_logger.info(f"[PDF STEP 3: PAGE SAVED] Page {page_idx + 1}/{len(doc)} saved to '{img_path}' ({pix.width}x{pix.height}px)")
                except Exception as page_err:
                    pdf_logger.error(f"[PDF PAGE ERROR] Failed rendering page {page_idx + 1}: {page_err}")

            doc.close()
        except Exception as e:
            pdf_logger.error(f"[PDF RENDER EXCEPTION] Failed reading PDF document '{pdf_path}': {e}")

        return rendered_paths

    def extract_hd_crops(self, pdf_path: str, dpi: int = 300) -> Dict[str, str]:
        """Extract specialized high-resolution crops targeting key engineering regions with boundary clamping and error handling."""
        pdf_logger.info("=" * 80)
        pdf_logger.info(f"[PDF STEP 4: HD CROPS START] Extracting HD ROI crops from '{pdf_path}' at DPI={dpi}")
        pdf_logger.info("=" * 80)

        crop_paths: Dict[str, str] = {}

        if not pdf_path or not os.path.exists(pdf_path):
            pdf_logger.error(f"[PDF STEP 4: NOT FOUND] PDF file not found at: '{pdf_path}'")
            return crop_paths

        try:
            file_size = os.path.getsize(pdf_path)
            if file_size == 0:
                pdf_logger.error(f"[PDF STEP 4: EMPTY] PDF file is 0 bytes: '{pdf_path}'")
                return crop_paths

            doc = pymupdf.open(pdf_path)
            if len(doc) == 0:
                pdf_logger.error(f"[PDF STEP 4: NO PAGES] PDF document has 0 pages.")
                doc.close()
                return crop_paths

            page = doc[0]  # First sheet
            rect = page.rect  # width, height
            pdf_logger.info(f"[PDF STEP 4a: SHEET GEOMETRY] Page 1 rect: width={rect.width:.1f}pt, height={rect.height:.1f}pt")

            safe_dpi = max(72, min(400, int(dpi))) if dpi else 300
            zoom = safe_dpi / 72.0
            mat = pymupdf.Matrix(zoom, zoom)

            base_name = os.path.splitext(os.path.basename(pdf_path))[0]

            # 1. Schedule Table Crop (Right 45% of the sheet) with boundary clamping
            x0_sched = max(0.0, min(rect.width * 0.55, rect.width - 10))
            y0_sched = max(0.0, min(rect.height * 0.05, rect.height - 10))
            x1_sched = min(rect.width, max(x0_sched + 10, rect.width * 0.98))
            y1_sched = min(rect.height, max(y0_sched + 10, rect.height * 0.95))

            try:
                sched_rect = pymupdf.Rect(x0_sched, y0_sched, x1_sched, y1_sched)
                pix_sched = page.get_pixmap(matrix=mat, clip=sched_rect, alpha=False)
                sched_path = os.path.join(self.output_dir, f"{base_name}_crop_schedule.png")
                pix_sched.save(sched_path)
                crop_paths["schedule_table"] = sched_path
                pdf_logger.info(
                    f"[PDF STEP 4b: SCHEDULE TABLE CROP] Saved schedule crop to '{sched_path}' "
                    f"({pix_sched.width}x{pix_sched.height}px, clip: x={sched_rect.x0:.0f}..{sched_rect.x1:.0f}, y={sched_rect.y0:.0f}..{sched_rect.y1:.0f})"
                )
            except Exception as sched_err:
                pdf_logger.error(f"[PDF CROP ERROR] Error creating schedule crop: {sched_err}")

            # 2. Rebar Cross-Section Detail Crop (Lower 45% section) with boundary clamping
            x0_rebar = max(0.0, min(rect.width * 0.02, rect.width - 10))
            y0_rebar = max(0.0, min(rect.height * 0.55, rect.height - 10))
            x1_rebar = min(rect.width, max(x0_rebar + 10, rect.width * 0.60))
            y1_rebar = min(rect.height, max(y0_rebar + 10, rect.height * 0.98))

            try:
                rebar_rect = pymupdf.Rect(x0_rebar, y0_rebar, x1_rebar, y1_rebar)
                pix_rebar = page.get_pixmap(matrix=mat, clip=rebar_rect, alpha=False)
                rebar_path = os.path.join(self.output_dir, f"{base_name}_crop_sections.png")
                pix_rebar.save(rebar_path)
                crop_paths["rebar_sections"] = rebar_path
                pdf_logger.info(
                    f"[PDF STEP 4c: REBAR SECTIONS CROP] Saved rebar sections crop to '{rebar_path}' "
                    f"({pix_rebar.width}x{pix_rebar.height}px, clip: x={rebar_rect.x0:.0f}..{rebar_rect.x1:.0f}, y={rebar_rect.y0:.0f}..{rebar_rect.y1:.0f})"
                )
            except Exception as rebar_err:
                pdf_logger.error(f"[PDF CROP ERROR] Error creating rebar sections crop: {rebar_err}")

            # 3. Overall Full Page Overview (Lower DPI for context)
            try:
                overview_mat = pymupdf.Matrix(100 / 72.0, 100 / 72.0)
                pix_overview = page.get_pixmap(matrix=overview_mat, alpha=False)
                overview_path = os.path.join(self.output_dir, f"{base_name}_overview.png")
                pix_overview.save(overview_path)
                crop_paths["overview"] = overview_path
                pdf_logger.info(f"[PDF STEP 4d: OVERVIEW CROP] Saved overview image to '{overview_path}' ({pix_overview.width}x{pix_overview.height}px)")
            except Exception as ov_err:
                pdf_logger.error(f"[PDF CROP ERROR] Error creating overview crop: {ov_err}")

            doc.close()
        except Exception as e:
            pdf_logger.error(f"[PDF EXTRACTION EXCEPTION] Failed processing PDF crops: {e}")

        pdf_logger.info(f"[PDF STEP 4e: CROPS COMPLETE] Generated {len(crop_paths)} ROI crops successfully.")
        return crop_paths

    def encode_image_to_base64(self, image_path: str) -> str:
        """Encode image file to base64 string with defensive validation and error handling."""
        if not image_path or not os.path.exists(image_path):
            pdf_logger.error(f"[PDF STEP 5: FILE NOT FOUND] Image file not found: '{image_path}'")
            return ""

        try:
            file_size_kb = round(os.path.getsize(image_path) / 1024, 2)
            with open(image_path, "rb") as image_file:
                encoded = base64.b64encode(image_file.read()).decode("utf-8")
            
            pdf_logger.info(f"[PDF STEP 5: BASE64 ENCODE] Encoded '{image_path}' ({file_size_kb} KB) -> Base64 Length: {len(encoded)} chars")
            return encoded
        except Exception as e:
            pdf_logger.error(f"[PDF BASE64 ERROR] Failed reading image file '{image_path}': {e}")
            return ""


# Global PDF parser instance
pdf_vision_parser = PDFVisionParser()
