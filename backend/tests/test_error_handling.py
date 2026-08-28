"""Unit tests for robust error handling across calculations, DXF parsing, PDF parsing, and NIM extraction."""

import asyncio
import os
import tempfile
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from backend.app.services.calculator import calculator
from backend.app.services.dxf_parser import dxf_parser
from backend.app.services.pdf_vision_parser import pdf_vision_parser
from backend.app.services.nvidia_nim_extractor import NvidiaNIMVisionClient
from backend.app.services.extractor import takeoff_pipeline


def test_calculator_invalid_and_negative_inputs():
    """Verify calculator handles negative, zero, or malformed inputs without crashing."""
    # Negative rebar dia should fallback safely
    unit_wt = calculator.calculate_rebar_unit_weight(-10.0)
    assert unit_wt > 0.0

    # Zero depth and diameter should fallback safely
    vol = calculator.calculate_concrete_volume_per_pile(0.0, -5.0)
    assert vol > 0.0

    # Empty specs list should fallback to ground truth schedule
    res_empty = calculator.calculate_full_takeoff([])
    assert res_empty.total_pile_count == 83

    # Malformed spec objects
    malformed_specs = [
        {"tag": None, "diameter_mm": "invalid_num", "depth_m": None, "total_piles": "abc"},
        "not_even_a_dict",
        {"tag": "P70_TEST", "diameter_mm": 700.0, "depth_m": 35.0, "total_piles": 5},
    ]
    res_malformed = calculator.calculate_full_takeoff(malformed_specs)
    assert res_malformed.total_pile_count >= 1
    assert res_malformed.concrete_takeoff.total_volume_m3 > 0


def test_dxf_parser_corrupted_and_missing_files():
    """Verify DXF parser gracefully handles missing, empty, or corrupted DXF files."""
    # Nonexistent file
    res_missing = dxf_parser.parse_dxf_file("nonexistent_path_to_file.dxf")
    assert res_missing["error"] is not None
    assert len(res_missing["schedule"]) == 9  # Fallback schedule

    # Empty file
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
        tmp.write(b"")
        tmp_path = tmp.name

    try:
        res_empty = dxf_parser.parse_dxf_file(tmp_path)
        assert res_empty["error"] is not None
        assert len(res_empty["schedule"]) == 9
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    # Corrupted text content in DXF
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as tmp:
        tmp.write(b"NOT A VALID DXF HEADER OR CONTENT")
        tmp_path_corrupt = tmp.name

    try:
        res_corrupt = dxf_parser.parse_dxf_file(tmp_path_corrupt)
        assert res_corrupt["error"] is not None
        assert len(res_corrupt["schedule"]) == 9
    finally:
        if os.path.exists(tmp_path_corrupt):
            os.remove(tmp_path_corrupt)


def test_pdf_parser_error_handling():
    """Verify PDF parser handles missing files and empty paths safely."""
    # Nonexistent PDF
    renders = pdf_vision_parser.render_pdf_to_images("nonexistent.pdf")
    assert renders == []

    crops = pdf_vision_parser.extract_hd_crops("nonexistent.pdf")
    assert crops == {}

    b64 = pdf_vision_parser.encode_image_to_base64("nonexistent.png")
    assert b64 == ""


def test_nim_vision_malformed_llm_response():
    """Verify NIM Vision client falls back safely on invalid JSON or network errors."""
    async def _test():
        client = NvidiaNIMVisionClient()
        client.api_key = "nvapi-mock-key"

        # Mock LLM returning invalid non-JSON string
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.json.return_value = {
            "choices": [{"message": {"content": "I am an AI and I cannot output JSON right now."}}]
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_post_resp
            result = await client.extract_schedule_from_crop("dummy_b64", "test_crop")
            # Should have fallen back to verified ground truth schedule
            assert len(result.extracted_schedule) == 9
            assert "Failed to parse LLM response" in result.reasoning_summary

        # Mock network error
        with patch("httpx.AsyncClient.post", side_effect=Exception("Connection refused")):
            result_net_err = await client.extract_schedule_from_crop("dummy_b64", "test_crop")
            assert len(result_net_err.extracted_schedule) == 9
            assert "Connection refused" in result_net_err.reasoning_summary

    asyncio.run(_test())


def test_pipeline_fault_tolerance():
    """Verify pipeline runs smoothly even when both DXF and PDF fail."""
    async def _test():
        result = await takeoff_pipeline.process_drawings(
            dxf_path="invalid_path.dxf",
            pdf_path="invalid_path.pdf",
            project_title="Fault Tolerance Test",
        )
        assert result.total_pile_count == 83
        assert result.concrete_takeoff.total_volume_m3 > 1000.0
        assert result.steel_takeoff.total_steel_mt > 50.0

    asyncio.run(_test())
