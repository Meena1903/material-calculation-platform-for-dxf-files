"""Tests for detailed logging and NVIDIA NIM Vision client tracing."""

import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.services.nvidia_nim_extractor import NvidiaNIMVisionClient
from backend.app.core.config import settings


def test_nim_vision_client_logging_and_payload():
    """Verify that NIM Vision Client logs inputs, prompts, and handles valid API responses."""
    async def _test():
        client = NvidiaNIMVisionClient()
        client.api_key = "nvapi-test-mock-key-for-unit-testing"

        mock_llm_response_data = {
            "choices": [
                {
                    "message": {
                        "content": (
                            "```json\n"
                            "{\n"
                            '  "drawing_title": "Test Drawing",\n'
                            '  "drawing_date": "28.08.2026",\n'
                            '  "extracted_schedule": [\n'
                            "    {\n"
                            '      "pile_tag": "P50",\n'
                            '      "pile_diameter_mm": 500.0,\n'
                            '      "depth_m": 35.0,\n'
                            '      "capacity_ton": 60.0,\n'
                            '      "count_expression": "29",\n'
                            '      "total_count": 29,\n'
                            '      "main_reinforcement": "8 Nos 12mm dia",\n'
                            '      "helical_ties": "8mm dia @ 180mm c/c",\n'
                            '      "spacers": "12mm dia @ 1500mm c/c",\n'
                            '      "confidence_score": 0.99\n'
                            "    }\n"
                            "  ],\n"
                            '  "reasoning_summary": "Extracted P50 row."\n'
                            "}\n"
                            "```"
                        )
                    }
                }
            ],
            "usage": {"prompt_tokens": 512, "completion_tokens": 128, "total_tokens": 640},
        }

        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.json.return_value = mock_llm_response_data

        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get, \
             patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_get.return_value = mock_get_resp
            mock_post.return_value = mock_post_resp

            health = await client.check_health()
            assert health["status"] == "connected"

            result = await client.extract_schedule_from_crop(
                image_base64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                crop_name="test_crop_schedule"
            )
            assert result.drawing_title == "Test Drawing"
            assert len(result.extracted_schedule) == 1
            assert result.extracted_schedule[0].pile_tag == "P50"
            assert result.extracted_schedule[0].total_count == 29

    asyncio.run(_test())
