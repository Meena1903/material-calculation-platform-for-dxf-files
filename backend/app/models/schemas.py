"""Pydantic schemas and data models for Pile Foundation Takeoff Engine."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RebarBarDetail(BaseModel):
    """Specification of a single rebar component (Main Bar, Spiral Link, or Spacer Ring)."""
    bar_type: str = Field(description="Role: 'Main Longitudinal', 'Helical Tie / Spiral', or 'Spacer Ring'")
    diameter_mm: float = Field(description="Nominal diameter in millimeters (e.g., 12, 16, 20)")
    count_or_pitch_description: str = Field(description="Text description (e.g., '8 Nos', '@180mm c/c', '@1500mm c/c')")
    bar_count_per_pile: int = Field(default=1, description="Number of bars per pile if discrete")
    unit_weight_kg_per_m: float = Field(description="Calculated via d^2 / 162.28 in native Python")
    cut_length_per_pile_m: float = Field(description="Calculated cut length per pile in meters")
    total_length_per_pile_m: float = Field(description="Total linear meters per pile")
    total_weight_per_pile_kg: float = Field(description="Total steel weight per pile in kg")
    total_weight_all_piles_kg: float = Field(description="Total steel weight for all piles of this type in kg")
    total_weight_all_piles_mt: float = Field(description="Total steel weight in Metric Tons (MT)")


class PileTypeInventory(BaseModel):
    """Structured representation of a Pile Type from drawings & schedules."""
    tag: str = Field(description="Pile tag or designation (e.g., P50, P70A, P90, 2P70, 2P80, 2P90, 3P80, 4P80, 10P70)")
    diameter_mm: float = Field(description="Pile diameter in millimeters (e.g., 500, 700, 800, 900)")
    diameter_m: float = Field(description="Pile diameter in meters")
    depth_m: float = Field(description="Pile cutoff depth / embedment length in meters (e.g., 35m, 45m)")
    capacity_ton: float = Field(description="Safe working load capacity in Metric Tons (e.g., 60T, 90T, 150T, 180T, 225T)")
    group_multiplier: int = Field(default=1, description="Number of piles per cap (e.g. 1 for P50, 2 for 2P70, 4 for 4P80, 10 for 10P70)")
    cap_count: int = Field(default=1, description="Number of pile cap instances (e.g., 8 for 2P80)")
    total_piles: int = Field(description="Total pile count for this type = cap_count * group_multiplier")
    shape: str = Field(default="Circular", description="Geometric cross-section shape")
    concrete_grade: str = Field(default="M35", description="Design concrete mix grade")
    steel_grade: str = Field(default="Fe500D", description="Design steel rebar grade")
    concrete_volume_per_pile_m3: float = Field(description="Volume per pile: pi * (d/2)^2 * L in m³")
    total_concrete_volume_m3: float = Field(description="Total RMC concrete volume in m³")
    rebar_details: List[RebarBarDetail] = Field(default_factory=list, description="BBS component breakdown")
    total_steel_weight_per_pile_kg: float = Field(default=0.0, description="Total steel kg per pile")
    total_steel_tonnage_mt: float = Field(default=0.0, description="Total steel in Metric Tons (MT)")


class ConcreteTakeoffSummary(BaseModel):
    """RMC Concrete Volumetric Takeoff summary."""
    total_volume_m3: float = Field(description="Total theoretical concrete volume in m³")
    volume_with_5pct_wastage_m3: float = Field(description="Concrete volume including 5% overbreak / wastage")
    volume_by_diameter_m3: Dict[str, float] = Field(default_factory=dict, description="Concrete volume breakdown by diameter")
    volume_by_pile_type_m3: Dict[str, float] = Field(default_factory=dict, description="Concrete volume breakdown by pile tag")


class SteelTakeoffSummary(BaseModel):
    """Bar Bending Schedule (BBS) Steel Reinforcement summary."""
    total_steel_kg: float = Field(description="Total steel weight in kg")
    total_steel_mt: float = Field(description="Total steel weight in Metric Tons (MT)")
    steel_by_bar_dia_mt: Dict[str, float] = Field(default_factory=dict, description="Weight breakdown by bar diameter (e.g., '12mm', '16mm', '20mm', '8mm')")
    steel_by_component_mt: Dict[str, float] = Field(default_factory=dict, description="Weight breakdown by role (Main, Helical, Spacer)")
    steel_by_pile_type_mt: Dict[str, float] = Field(default_factory=dict, description="Weight breakdown by pile tag")


class ManpowerEstimate(BaseModel):
    """Labor and Productivity Man-Days Estimation based on exact engineering constants."""
    piling_and_concreting_mandays: float = Field(description="0.25 Man-Days per m³ concrete")
    rebar_fabrication_mandays: float = Field(description="2.50 Man-Days per MT steel")
    pile_head_chipping_mandays: float = Field(description="0.50 Man-Days per pile")
    total_mandays: float = Field(description="Sum of all activities in Man-Days")
    formula_basis: Dict[str, str] = Field(default_factory=dict, description="Explanation of calculation basis")


class BOQItem(BaseModel):
    """Bill of Quantities (BOQ) standard line item."""
    item_no: str = Field(description="Item sequence number (e.g., '1.01', '2.01')")
    description: str = Field(description="Detailed civil engineering specification")
    quantity: float = Field(description="Calculated quantity")
    unit: str = Field(description="Measurement unit (e.g., 'Nos', 'm³', 'MT', 'Man-Days')")
    estimated_rate_inr: float = Field(default=0.0, description="Estimated benchmark unit rate in INR")
    estimated_amount_inr: float = Field(default=0.0, description="Total amount in INR")


class CADVisualEntity(BaseModel):
    """Vector CAD entity for 2D visual layout rendering on React frontend."""
    id: str
    entity_type: str  # CIRCLE, INSERT, TEXT, LINE, etc.
    layer: str
    center_x: float
    center_y: float
    radius: Optional[float] = None
    diameter_mm: Optional[float] = None
    tag: Optional[str] = None
    group_type: Optional[str] = None
    color: Optional[str] = None


class NIMVisualExtractionItem(BaseModel):
    """Pydantic schema for structured extraction from NVIDIA NIM Multimodal Vision model."""
    pile_tag: str
    pile_diameter_mm: float
    depth_m: float
    capacity_ton: Optional[float] = None
    count_expression: Optional[str] = None
    total_count: int
    main_reinforcement: Optional[str] = None
    helical_ties: Optional[str] = None
    spacers: Optional[str] = None
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)


class NIMVisualExtractionResponse(BaseModel):
    """Structured response from NVIDIA NIM Vision API for localized table/drawing crops."""
    drawing_title: Optional[str] = None
    drawing_date: Optional[str] = None
    extracted_schedule: List[NIMVisualExtractionItem] = Field(default_factory=list)
    model_used: str = ""
    reasoning_summary: Optional[str] = None
    is_valid_schema: bool = True


class TakeoffResult(BaseModel):
    """Complete consolidated takeoff and analysis output."""
    project_title: str = "BuildIQ Pile Foundation Takeoff Engine"
    source_files: List[str] = Field(default_factory=list)
    total_pile_count: int
    pile_inventory: List[PileTypeInventory]
    concrete_takeoff: ConcreteTakeoffSummary
    steel_takeoff: SteelTakeoffSummary
    manpower_estimation: ManpowerEstimate
    boq_items: List[BOQItem]
    cad_entities: List[CADVisualEntity] = Field(default_factory=list)
    bounding_box: Dict[str, float] = Field(default_factory=dict)
    nim_extraction_info: Optional[NIMVisualExtractionResponse] = None
    calculation_engine: str = "Native Python 3.14 (IS 1786 / SP 34 compliant, 100% deterministic)"
