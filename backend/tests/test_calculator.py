"""Unit tests for Native Python Engineering Calculator."""

import math
import pytest
from backend.app.services.calculator import calculator
from backend.app.core.config import settings


def test_rebar_unit_weight_formula():
    """Verify IS 1786 unit weight formula w = d^2 / 162.28 kg/m."""
    # 8mm bar: 8^2 / 162.28 = 64 / 162.28 = 0.3944 kg/m
    assert pytest.approx(calculator.calculate_rebar_unit_weight(8.0), 0.001) == 0.3944
    # 12mm bar: 144 / 162.28 = 0.8874 kg/m
    assert pytest.approx(calculator.calculate_rebar_unit_weight(12.0), 0.001) == 0.8874
    # 16mm bar: 256 / 162.28 = 1.5775 kg/m
    assert pytest.approx(calculator.calculate_rebar_unit_weight(16.0), 0.001) == 1.5775
    # 20mm bar: 400 / 162.28 = 2.4649 kg/m
    assert pytest.approx(calculator.calculate_rebar_unit_weight(20.0), 0.001) == 2.4649


def test_concrete_volume_formula():
    """Verify circular cylinder volume formula V = pi * (d/2)^2 * L."""
    # 500mm dia, 35m depth
    # Area = pi * 0.25^2 = 0.19635 m2
    # Volume = 0.19635 * 35 = 6.8722 m3
    vol_500 = calculator.calculate_concrete_volume_per_pile(500.0, 35.0)
    assert pytest.approx(vol_500, 0.01) == 6.8722

    # 700mm dia, 45m depth
    # Area = pi * 0.35^2 = 0.38485 m2
    # Volume = 0.38485 * 45 = 17.3180 m3
    vol_700 = calculator.calculate_concrete_volume_per_pile(700.0, 45.0)
    assert pytest.approx(vol_700, 0.01) == 17.3180

    # 800mm dia, 45m depth
    # Area = pi * 0.40^2 = 0.50265 m2
    # Volume = 0.50265 * 45 = 22.6195 m3
    vol_800 = calculator.calculate_concrete_volume_per_pile(800.0, 45.0)
    assert pytest.approx(vol_800, 0.01) == 22.6195

    # 900mm dia, 45m depth
    # Area = pi * 0.45^2 = 0.63617 m2
    # Volume = 0.63617 * 45 = 28.6278 m3
    vol_900 = calculator.calculate_concrete_volume_per_pile(900.0, 45.0)
    assert pytest.approx(vol_900, 0.01) == 28.6278


def test_manpower_estimation_ratios():
    """Verify manpower ratios: 0.25 days/m3, 2.50 days/MT, 0.50 days/pile."""
    sample_specs = [
        {"tag": "P50", "diameter_mm": 500.0, "depth_m": 35.0, "total_piles": 10},
    ]
    result = calculator.calculate_full_takeoff(sample_specs)
    
    vol = result.concrete_takeoff.total_volume_m3
    steel_mt = result.steel_takeoff.total_steel_mt
    piles = result.total_pile_count

    expected_piling = round(vol * 0.25, 2)
    expected_rebar = round(steel_mt * 2.50, 2)
    expected_chipping = round(piles * 0.50, 2)

    assert result.manpower_estimation.piling_and_concreting_mandays == expected_piling
    assert result.manpower_estimation.rebar_fabrication_mandays == expected_rebar
    assert result.manpower_estimation.pile_head_chipping_mandays == expected_chipping
    assert result.manpower_estimation.total_mandays == round(expected_piling + expected_rebar + expected_chipping, 2)


def test_full_ground_truth_takeoff_counts():
    """Verify that full foundation schedule aggregates to exactly 83 piles and positive quantities."""
    schedule = [
        {"tag": "P50", "diameter_mm": 500.0, "depth_m": 35.0, "total_piles": 29},
        {"tag": "P70A", "diameter_mm": 700.0, "depth_m": 35.0, "total_piles": 2},
        {"tag": "P90", "diameter_mm": 900.0, "depth_m": 45.0, "total_piles": 1},
        {"tag": "2P70", "diameter_mm": 700.0, "depth_m": 45.0, "total_piles": 10},
        {"tag": "2P80", "diameter_mm": 800.0, "depth_m": 45.0, "total_piles": 16},
        {"tag": "2P90", "diameter_mm": 900.0, "depth_m": 45.0, "total_piles": 8},
        {"tag": "3P80", "diameter_mm": 800.0, "depth_m": 45.0, "total_piles": 3},
        {"tag": "4P80", "diameter_mm": 800.0, "depth_m": 45.0, "total_piles": 4},
        {"tag": "10P70", "diameter_mm": 700.0, "depth_m": 45.0, "total_piles": 10},
    ]
    result = calculator.calculate_full_takeoff(schedule)

    assert result.total_pile_count == 83
    assert pytest.approx(result.concrete_takeoff.total_volume_m3, 0.01) == 1350.491
    assert result.steel_takeoff.total_steel_mt > 50.0
    assert result.manpower_estimation.total_mandays > 400.0
    assert len(result.boq_items) >= 5
