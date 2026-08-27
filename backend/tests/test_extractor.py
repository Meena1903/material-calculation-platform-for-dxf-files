"""Unit tests for extractor and DXF parsing services."""

import os
import pytest
from backend.app.services.dxf_parser import dxf_parser
from backend.app.services.calculator import calculator


def test_dxf_ground_truth_schedule():
    """Verify ground truth schedule specification."""
    sched = dxf_parser.ground_truth_schedule
    assert len(sched) == 9
    total = sum(item["total_piles"] for item in sched)
    assert total == 83


def test_group_multiplier_parsing():
    from backend.app.services.extractor import takeoff_pipeline
    assert takeoff_pipeline._parse_group_multiplier("P50") == 1
    assert takeoff_pipeline._parse_group_multiplier("2P70") == 2
    assert takeoff_pipeline._parse_group_multiplier("3P80") == 3
    assert takeoff_pipeline._parse_group_multiplier("4P80") == 4
    assert takeoff_pipeline._parse_group_multiplier("10P70") == 10
