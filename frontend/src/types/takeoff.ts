export interface RebarBarDetail {
  bar_type: string;
  diameter_mm: number;
  count_or_pitch_description: string;
  bar_count_per_pile: number;
  unit_weight_kg_per_m: number;
  cut_length_per_pile_m: number;
  total_length_per_pile_m: number;
  total_weight_per_pile_kg: number;
  total_weight_all_piles_kg: number;
  total_weight_all_piles_mt: number;
}

export interface PileTypeInventory {
  tag: string;
  diameter_mm: number;
  diameter_m: number;
  depth_m: number;
  capacity_ton: number;
  group_multiplier: number;
  cap_count: number;
  total_piles: number;
  shape: string;
  concrete_grade: string;
  steel_grade: string;
  concrete_volume_per_pile_m3: number;
  total_concrete_volume_m3: number;
  rebar_details: RebarBarDetail[];
  total_steel_weight_per_pile_kg: number;
  total_steel_tonnage_mt: number;
}

export interface ConcreteTakeoffSummary {
  total_volume_m3: number;
  volume_with_5pct_wastage_m3: number;
  volume_by_diameter_m3: Record<string, number>;
  volume_by_pile_type_m3: Record<string, number>;
}

export interface SteelTakeoffSummary {
  total_steel_kg: number;
  total_steel_mt: number;
  steel_by_bar_dia_mt: Record<string, number>;
  steel_by_component_mt: Record<string, number>;
  steel_by_pile_type_mt: Record<string, number>;
}

export interface ManpowerEstimate {
  piling_and_concreting_mandays: number;
  rebar_fabrication_mandays: number;
  pile_head_chipping_mandays: number;
  total_mandays: number;
  formula_basis: Record<string, string>;
}

export interface BOQItem {
  item_no: string;
  description: string;
  quantity: number;
  unit: string;
  estimated_rate_inr: number;
  estimated_amount_inr: number;
}

export interface CADVisualEntity {
  id: string;
  entity_type: string;
  layer: string;
  center_x: number;
  center_y: number;
  radius?: number;
  diameter_mm?: number;
  tag?: string;
  group_type?: string;
  color?: string;
}

export interface NIMVisualExtractionItem {
  pile_tag: string;
  pile_diameter_mm: number;
  depth_m: number;
  capacity_ton?: number;
  count_expression?: string;
  total_count: number;
  main_reinforcement?: string;
  helical_ties?: string;
  spacers?: string;
  confidence_score: number;
}

export interface NIMVisualExtractionResponse {
  drawing_title?: string;
  drawing_date?: string;
  extracted_schedule: NIMVisualExtractionItem[];
  model_used: string;
  reasoning_summary?: string;
  is_valid_schema: boolean;
}

export interface TakeoffResult {
  project_title: string;
  source_files: string[];
  total_pile_count: number;
  pile_inventory: PileTypeInventory[];
  concrete_takeoff: ConcreteTakeoffSummary;
  steel_takeoff: SteelTakeoffSummary;
  manpower_estimation: ManpowerEstimate;
  boq_items: BOQItem[];
  cad_entities: CADVisualEntity[];
  bounding_box: {
    min_x?: number;
    min_y?: number;
    max_x?: number;
    max_y?: number;
    width?: number;
    height?: number;
  };
  nim_extraction_info?: NIMVisualExtractionResponse;
  calculation_engine: string;
}

export interface HealthResponse {
  status: string;
  app_name: string;
  environment: string;
  nvidia_nim: {
    status: string;
    message: string;
    model: string;
  };
  calculation_engine: string;
}
