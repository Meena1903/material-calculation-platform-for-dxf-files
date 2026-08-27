"""Unit tests for Pydantic models serialization and validation."""

import pytest
from backend.app.models.schemas import (
    RebarBarDetail,
    PileTypeInventory,
    ConcreteTakeoffSummary,
    SteelTakeoffSummary,
    ManpowerEstimate,
    BOQItem,
    TakeoffResult,
)


def test_schema_serialization():
    detail = RebarBarDetail(
        bar_type="Main Longitudinal",
        diameter_mm=16.0,
        count_or_pitch_description="8 Nos 16mm dia",
        bar_count_per_pile=8,
        unit_weight_kg_per_m=1.5775,
        cut_length_per_pile_m=46.0,
        total_length_per_pile_m=368.0,
        total_weight_per_pile_kg=580.52,
        total_weight_all_piles_kg=5805.2,
        total_weight_all_piles_mt=5.8052,
    )
    assert detail.diameter_mm == 16.0
    assert detail.unit_weight_kg_per_m == 1.5775
    d_dict = detail.model_dump()
    assert d_dict["bar_type"] == "Main Longitudinal"
