"""Native Python Engineering Calculator for Pile Foundations.

CRITICAL ENGINEERING CONSTRAINT:
100% of mathematical calculations, volumetric extrusions, BBS unit weights,
and manpower estimations must execute strictly in native deterministic Python.
No LLM/Vision hallucination is permitted in this module.
"""

import math
from typing import List, Dict, Tuple, Any
from backend.app.core.config import settings
from backend.app.models.schemas import (
    RebarBarDetail,
    PileTypeInventory,
    ConcreteTakeoffSummary,
    SteelTakeoffSummary,
    ManpowerEstimate,
    BOQItem,
    TakeoffResult,
)


class PileTakeoffCalculator:
    """Deterministic, high-precision Civil Engineering Takeoff Calculator."""

    def __init__(
        self,
        clear_cover_mm: float = settings.DEFAULT_CLEAR_COVER_MM,
        steel_unit_weight_denominator: float = settings.UNIT_WEIGHT_STEEL_DENOMINATOR,
        manpower_piling_per_m3: float = settings.MANPOWER_PILING_CONCRETE_PER_M3,
        manpower_rebar_per_mt: float = settings.MANPOWER_REBAR_PER_MT,
        manpower_chipping_per_pile: float = settings.MANPOWER_CHIPPING_PER_PILE,
    ):
        self.clear_cover_mm = clear_cover_mm
        self.clear_cover_m = clear_cover_mm / 1000.0
        self.denominator = steel_unit_weight_denominator
        self.manpower_piling_rate = manpower_piling_per_m3
        self.manpower_rebar_rate = manpower_rebar_per_mt
        self.manpower_chipping_rate = manpower_chipping_per_pile

    def calculate_rebar_unit_weight(self, diameter_mm: float) -> float:
        """Standard IS 1786 unit weight formula: w = d^2 / 162.28 (kg/m)."""
        return round((diameter_mm ** 2) / self.denominator, 4)

    def calculate_concrete_volume_per_pile(self, diameter_mm: float, depth_m: float) -> float:
        """Volume of a circular pile: V = pi * (d / 2)^2 * L (m³)."""
        radius_m = (diameter_mm / 1000.0) / 2.0
        area_m2 = math.pi * (radius_m ** 2)
        volume_m3 = area_m2 * depth_m
        return round(volume_m3, 4)

    def calculate_helical_tie_length_per_pile(
        self, pile_diameter_mm: float, depth_m: float, pitch_mm: float = 180.0
    ) -> float:
        """Calculate total developed length of spiral / helical tie cage in meters.
        
        Cage diameter = Pile diameter - 2 * clear cover
        Length per turn = sqrt((pi * D_cage)^2 + pitch^2)
        Total length = (depth / pitch) * length_per_turn + 2 anchor turns at top/bottom.
        """
        cage_diameter_m = (pile_diameter_mm - (2.0 * self.clear_cover_mm)) / 1000.0
        if cage_diameter_m <= 0:
            cage_diameter_m = (pile_diameter_mm * 0.8) / 1000.0

        pitch_m = pitch_mm / 1000.0
        circ_cage = math.pi * cage_diameter_m
        turn_length_m = math.sqrt((circ_cage ** 2) + (pitch_m ** 2))
        number_of_turns = depth_m / pitch_m
        # Add 2 additional closed turns for anchorage at head & toe
        total_length_m = (number_of_turns + 2.0) * turn_length_m
        return round(total_length_m, 3)

    def calculate_spacer_ring_length_per_pile(
        self, pile_diameter_mm: float, depth_m: float, spacing_mm: float = 1500.0
    ) -> Tuple[int, float]:
        """Calculate stiffener/spacer rings count and linear length in meters.
        
        Spacer ring circumference = pi * Cage diameter + 150mm overlap
        Count = floor(depth / 1.5m) + 1
        """
        cage_diameter_m = (pile_diameter_mm - (2.0 * self.clear_cover_mm)) / 1000.0
        if cage_diameter_m <= 0:
            cage_diameter_m = (pile_diameter_mm * 0.8) / 1000.0

        num_rings = math.floor((depth_m * 1000.0) / spacing_mm) + 1
        ring_length_m = (math.pi * cage_diameter_m) + 0.15  # 150mm lap
        total_spacer_length_m = num_rings * ring_length_m
        return num_rings, round(total_spacer_length_m, 3)

    def build_rebar_schedule_for_pile(
        self,
        tag: str,
        diameter_mm: float,
        depth_m: float,
        total_piles: int,
        raw_rebar_spec: Dict[str, Any] = None,
    ) -> Tuple[List[RebarBarDetail], float, float]:
        """Build detailed BBS (Bar Bending Schedule) for a given pile type."""
        rebar_details: List[RebarBarDetail] = []
        total_steel_kg_per_pile = 0.0

        # Anchor projection length into pile cap (1.0m standard development length Ld)
        anchorage_into_cap_m = 1.0
        main_cut_length_m = depth_m + anchorage_into_cap_m

        # Resolve rebar configuration per pile diameter/tag based on drawing notes
        # 1. Main longitudinal bars
        if raw_rebar_spec and "main_bars" in raw_rebar_spec:
            main_bars_config = raw_rebar_spec["main_bars"]
        elif diameter_mm == 500:
            # P50 (60T): 8 Nos 12mm dia
            main_bars_config = [{"dia": 12.0, "count": 8, "desc": "8 Nos 12mm dia"}]
        elif diameter_mm == 700:
            # P70A / 2P70 / 10P70 (90T/150T): 8 Nos 16mm dia
            main_bars_config = [{"dia": 16.0, "count": 8, "desc": "8 Nos 16mm dia"}]
        elif diameter_mm == 800:
            # 2P80 / 3P80 / 4P80 (150T/180T): 10 Nos 16mm dia
            main_bars_config = [{"dia": 16.0, "count": 10, "desc": "10 Nos 16mm dia"}]
        elif diameter_mm == 900:
            # P90 / 2P90 (225T): 5 Nos 20mm dia + 5 Nos 16mm dia
            main_bars_config = [
                {"dia": 20.0, "count": 5, "desc": "5 Nos 20mm dia"},
                {"dia": 16.0, "count": 5, "desc": "5 Nos 16mm dia"},
            ]
        else:
            # Default fallback proportional to diameter
            count = max(6, int(diameter_mm / 100) + 2)
            dia = 16.0
            main_bars_config = [{"dia": dia, "count": count, "desc": f"{count} Nos {int(dia)}mm dia"}]

        for mb in main_bars_config:
            bar_dia = mb["dia"]
            bar_cnt = mb["count"]
            unit_wt = self.calculate_rebar_unit_weight(bar_dia)
            total_lin_m = bar_cnt * main_cut_length_m
            weight_per_pile_kg = round(total_lin_m * unit_wt, 3)
            weight_all_piles_kg = round(weight_per_pile_kg * total_piles, 3)
            weight_all_piles_mt = round(weight_all_piles_kg / 1000.0, 4)
            total_steel_kg_per_pile += weight_per_pile_kg

            rebar_details.append(
                RebarBarDetail(
                    bar_type="Main Longitudinal",
                    diameter_mm=bar_dia,
                    count_or_pitch_description=mb["desc"],
                    bar_count_per_pile=bar_cnt,
                    unit_weight_kg_per_m=unit_wt,
                    cut_length_per_pile_m=main_cut_length_m,
                    total_length_per_pile_m=round(total_lin_m, 2),
                    total_weight_per_pile_kg=weight_per_pile_kg,
                    total_weight_all_piles_kg=weight_all_piles_kg,
                    total_weight_all_piles_mt=weight_all_piles_mt,
                )
            )

        # 2. Helical ties / Spiral stirrups (8mm @ 180mm c/c)
        tie_dia = 8.0
        tie_pitch_mm = 180.0
        tie_unit_wt = self.calculate_rebar_unit_weight(tie_dia)
        tie_total_length_m = self.calculate_helical_tie_length_per_pile(diameter_mm, depth_m, tie_pitch_mm)
        tie_wt_per_pile_kg = round(tie_total_length_m * tie_unit_wt, 3)
        tie_wt_all_kg = round(tie_wt_per_pile_kg * total_piles, 3)
        tie_wt_all_mt = round(tie_wt_all_kg / 1000.0, 4)
        total_steel_kg_per_pile += tie_wt_per_pile_kg

        rebar_details.append(
            RebarBarDetail(
                bar_type="Helical Tie / Spiral",
                diameter_mm=tie_dia,
                count_or_pitch_description=f"8mm dia @ {int(tie_pitch_mm)}mm c/c",
                bar_count_per_pile=1,
                unit_weight_kg_per_m=tie_unit_wt,
                cut_length_per_pile_m=tie_total_length_m,
                total_length_per_pile_m=tie_total_length_m,
                total_weight_per_pile_kg=tie_wt_per_pile_kg,
                total_weight_all_piles_kg=tie_wt_all_kg,
                total_weight_all_piles_mt=tie_wt_all_mt,
            )
        )

        # 3. Spacer / Stiffener Rings (12mm @ 1500mm c/c)
        spacer_dia = 12.0
        spacer_spacing_mm = 1500.0
        spacer_unit_wt = self.calculate_rebar_unit_weight(spacer_dia)
        num_spacers, spacer_total_len_m = self.calculate_spacer_ring_length_per_pile(
            diameter_mm, depth_m, spacer_spacing_mm
        )
        spacer_wt_per_pile_kg = round(spacer_total_len_m * spacer_unit_wt, 3)
        spacer_wt_all_kg = round(spacer_wt_per_pile_kg * total_piles, 3)
        spacer_wt_all_mt = round(spacer_wt_all_kg / 1000.0, 4)
        total_steel_kg_per_pile += spacer_wt_per_pile_kg

        rebar_details.append(
            RebarBarDetail(
                bar_type="Spacer Ring",
                diameter_mm=spacer_dia,
                count_or_pitch_description=f"{num_spacers} Nos (12mm dia @ {int(spacer_spacing_mm)}mm c/c)",
                bar_count_per_pile=num_spacers,
                unit_weight_kg_per_m=spacer_unit_wt,
                cut_length_per_pile_m=round(spacer_total_len_m / num_spacers if num_spacers > 0 else 0, 3),
                total_length_per_pile_m=spacer_total_len_m,
                total_weight_per_pile_kg=spacer_wt_per_pile_kg,
                total_weight_all_piles_kg=spacer_wt_all_kg,
                total_weight_all_piles_mt=spacer_wt_all_mt,
            )
        )

        total_steel_tonnage_mt = round((total_steel_kg_per_pile * total_piles) / 1000.0, 4)
        return rebar_details, round(total_steel_kg_per_pile, 3), total_steel_tonnage_mt

    def calculate_full_takeoff(
        self,
        raw_pile_specs: List[Dict[str, Any]],
        project_title: str = "Automated Pile Foundation Takeoff",
        source_files: List[str] = None,
    ) -> TakeoffResult:
        """Run complete 100% deterministic takeoff calculations across all piles."""
        pile_inventory: List[PileTypeInventory] = []
        total_piles_count = 0
        total_concrete_volume_m3 = 0.0
        total_steel_kg = 0.0
        total_steel_mt = 0.0

        vol_by_dia: Dict[str, float] = {}
        vol_by_tag: Dict[str, float] = {}
        steel_by_dia: Dict[str, float] = {}
        steel_by_comp: Dict[str, float] = {"Main Longitudinal": 0.0, "Helical Tie / Spiral": 0.0, "Spacer Ring": 0.0}
        steel_by_tag: Dict[str, float] = {}

        for spec in raw_pile_specs:
            tag = spec.get("tag", "P_UNK")
            dia_mm = float(spec.get("diameter_mm", 700.0))
            dia_m = round(dia_mm / 1000.0, 3)
            depth_m = float(spec.get("depth_m", 45.0))
            capacity = float(spec.get("capacity_ton", 90.0))
            group_mult = int(spec.get("group_multiplier", 1))
            cap_cnt = int(spec.get("cap_count", 1))
            total_pile_cnt = int(spec.get("total_piles", cap_cnt * group_mult))

            # Concrete volume
            vol_per_pile = self.calculate_concrete_volume_per_pile(dia_mm, depth_m)
            tot_vol = round(vol_per_pile * total_pile_cnt, 3)

            # Rebar BBS
            rebar_details, steel_kg_per_pile, steel_mt_type = self.build_rebar_schedule_for_pile(
                tag=tag,
                diameter_mm=dia_mm,
                depth_m=depth_m,
                total_piles=total_pile_cnt,
                raw_rebar_spec=spec.get("rebar_spec"),
            )

            # Accumulate totals
            total_piles_count += total_pile_cnt
            total_concrete_volume_m3 += tot_vol
            total_steel_kg += (steel_kg_per_pile * total_pile_cnt)
            total_steel_mt += steel_mt_type

            # Accumulate breakdowns
            dia_key = f"{int(dia_mm)}mm"
            vol_by_dia[dia_key] = round(vol_by_dia.get(dia_key, 0.0) + tot_vol, 3)
            vol_by_tag[tag] = tot_vol
            steel_by_tag[tag] = steel_mt_type

            for detail in rebar_details:
                b_dia_key = f"{int(detail.diameter_mm)}mm"
                steel_by_dia[b_dia_key] = round(steel_by_dia.get(b_dia_key, 0.0) + detail.total_weight_all_piles_mt, 4)
                steel_by_comp[detail.bar_type] = round(
                    steel_by_comp.get(detail.bar_type, 0.0) + detail.total_weight_all_piles_mt, 4
                )

            pile_inventory.append(
                PileTypeInventory(
                    tag=tag,
                    diameter_mm=dia_mm,
                    diameter_m=dia_m,
                    depth_m=depth_m,
                    capacity_ton=capacity,
                    group_multiplier=group_mult,
                    cap_count=cap_cnt,
                    total_piles=total_pile_cnt,
                    shape="Circular",
                    concrete_grade=spec.get("concrete_grade", settings.DEFAULT_CONCRETE_GRADE),
                    steel_grade=spec.get("steel_grade", settings.DEFAULT_STEEL_GRADE),
                    concrete_volume_per_pile_m3=vol_per_pile,
                    total_concrete_volume_m3=tot_vol,
                    rebar_details=rebar_details,
                    total_steel_weight_per_pile_kg=steel_kg_per_pile,
                    total_steel_tonnage_mt=steel_mt_type,
                )
            )

        # Round consolidated summaries
        total_concrete_volume_m3 = round(total_concrete_volume_m3, 3)
        concrete_with_wastage = round(total_concrete_volume_m3 * 1.05, 3)
        total_steel_kg = round(total_steel_kg, 2)
        total_steel_mt = round(total_steel_mt, 4)

        concrete_summary = ConcreteTakeoffSummary(
            total_volume_m3=total_concrete_volume_m3,
            volume_with_5pct_wastage_m3=concrete_with_wastage,
            volume_by_diameter_m3=vol_by_dia,
            volume_by_pile_type_m3=vol_by_tag,
        )

        steel_summary = SteelTakeoffSummary(
            total_steel_kg=total_steel_kg,
            total_steel_mt=total_steel_mt,
            steel_by_bar_dia_mt=steel_by_dia,
            steel_by_component_mt=steel_by_comp,
            steel_by_pile_type_mt=steel_by_tag,
        )

        # Manpower calculations based on specified constants
        # 1. Piling & Concreting: 0.25 Man-Days per m³
        piling_mandays = round(total_concrete_volume_m3 * self.manpower_piling_rate, 2)
        # 2. Rebar Fabrication: 2.50 Man-Days per MT
        rebar_mandays = round(total_steel_mt * self.manpower_rebar_rate, 2)
        # 3. Pile Head Chipping: 0.50 Man-Days per pile
        chipping_mandays = round(total_piles_count * self.manpower_chipping_rate, 2)
        total_mandays = round(piling_mandays + rebar_mandays + chipping_mandays, 2)

        manpower = ManpowerEstimate(
            piling_and_concreting_mandays=piling_mandays,
            rebar_fabrication_mandays=rebar_mandays,
            pile_head_chipping_mandays=chipping_mandays,
            total_mandays=total_mandays,
            formula_basis={
                "piling_and_concreting": f"{self.manpower_piling_rate} Man-Days/m³ * {total_concrete_volume_m3} m³ = {piling_mandays} Man-Days",
                "rebar_fabrication": f"{self.manpower_rebar_rate} Man-Days/MT * {total_steel_mt} MT = {rebar_mandays} Man-Days",
                "pile_head_chipping": f"{self.manpower_chipping_rate} Man-Days/pile * {total_piles_count} piles = {chipping_mandays} Man-Days",
            },
        )

        # Generate standard BOQ Line Items
        boq_items = self.generate_boq_items(
            pile_inventory=pile_inventory,
            concrete_summary=concrete_summary,
            steel_summary=steel_summary,
            manpower=manpower,
        )

        return TakeoffResult(
            project_title=project_title,
            source_files=source_files or [],
            total_pile_count=total_piles_count,
            pile_inventory=pile_inventory,
            concrete_takeoff=concrete_summary,
            steel_takeoff=steel_summary,
            manpower_estimation=manpower,
            boq_items=boq_items,
        )

    def generate_boq_items(
        self,
        pile_inventory: List[PileTypeInventory],
        concrete_summary: ConcreteTakeoffSummary,
        steel_summary: SteelTakeoffSummary,
        manpower: ManpowerEstimate,
    ) -> List[BOQItem]:
        """Generate standard commercial civil BOQ items."""
        items: List[BOQItem] = []

        # 1. Piling Boring & Installation items
        for idx, p in enumerate(pile_inventory, start=1):
            rate = 3500.0 if p.diameter_mm >= 800 else 2800.0
            items.append(
                BOQItem(
                    item_no=f"1.{idx:02d}",
                    description=f"Boring and casting of {int(p.diameter_mm)}mm dia bored cast-in-situ RCC piles to depth {p.depth_m}m in all types of soil/weathered rock, including rig mobilization, casing, bentonite flushing, tremie placement of concrete Grade {p.concrete_grade} (Tag: {p.tag})",
                    quantity=float(p.total_piles),
                    unit="Nos",
                    estimated_rate_inr=rate * p.depth_m,
                    estimated_amount_inr=float(p.total_piles) * (rate * p.depth_m),
                )
            )

        # 2. Ready Mix Concrete (RMC) Supply
        items.append(
            BOQItem(
                item_no="2.01",
                description=f"Supplying and pumping design mix Ready Mixed Concrete ({settings.DEFAULT_CONCRETE_GRADE}) for bored cast-in-situ piles as per IS 456 / IS 2911 (Part 1/Sec 2), inclusive of admixture and slump retention",
                quantity=concrete_summary.total_volume_m3,
                unit="m³",
                estimated_rate_inr=6500.0,
                estimated_amount_inr=round(concrete_summary.total_volume_m3 * 6500.0, 2),
            )
        )

        # 3. High Yield Strength Deformed (HYSD / TMT) Steel Reinforcement
        items.append(
            BOQItem(
                item_no="3.01",
                description=f"Providing, straightening, cutting, bending, fabricating and placing in position thermo-mechanically treated ({settings.DEFAULT_STEEL_GRADE}) reinforcement bars in pile cages including spiral stirrups, stiffener rings, tack welding, binding wire and cover blocks as per IS 1786 and IS 2502",
                quantity=steel_summary.total_steel_mt,
                unit="MT",
                estimated_rate_inr=72000.0,
                estimated_amount_inr=round(steel_summary.total_steel_mt * 72000.0, 2),
            )
        )

        # 4. Pile Head Chipping & Trimming
        total_piles = sum(p.total_piles for p in pile_inventory)
        items.append(
            BOQItem(
                item_no="4.01",
                description="Chipping and breaking pile heads to cutoff level (COL) without damaging projecting rebar, cleaning, and preparing pile heads for cap integration",
                quantity=float(total_piles),
                unit="Nos",
                estimated_rate_inr=1200.0,
                estimated_amount_inr=float(total_piles) * 1200.0,
            )
        )

        # 5. Total Estimated Manpower
        items.append(
            BOQItem(
                item_no="5.01",
                description="Total site labor requirement for Piling, Concreting, Rebar cage fabrication, and Chipping",
                quantity=manpower.total_mandays,
                unit="Man-Days",
                estimated_rate_inr=850.0,
                estimated_amount_inr=round(manpower.total_mandays * 850.0, 2),
            )
        )

        return items


# Global calculator instance
calculator = PileTakeoffCalculator()
