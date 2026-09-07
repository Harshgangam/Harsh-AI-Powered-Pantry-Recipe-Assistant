export interface SubstitutionCandidate {
  missing_ingredient: string;
  substitute: string;
  ratio: string | null;
  confidence: 'high' | 'medium' | 'low';
  reason: string;
  use_case?: string | null;
  dietary_compatible: boolean;
  notes?: string | null;
  source?: string | null;
}



export interface ExplanationData {
  matched_ingredients: string[];
  missing_ingredients: string[];
  matched_count: number;
  total_recipe_ingredients: number;
  relevant_pantry_used_count: number;
  relevant_pantry_total_count: number;
  ims: number;
  pus: number;
  base_score?: number | null;
  final_score: number;

  why_this_recipe?: string;
  cuisine_bonus: number;
  time_adjustment: number;
  dietary_filter_applied?: string | null;
}

export interface RecipeRecommendationItem {
  recipe_id: number;
  title: string;
  ingredients: string[];
  directions: string[];
  link: string;
  source: string;
  ner: string[];
  matched_ingredients: string[];
  missing_ingredients: string[];
  missing_count: number;
  missing_categorized?: {
    essential: string[];
    optional: string[];
  };
  can_prepare_without_missing?: boolean;
  substitutions: SubstitutionCandidate[];
  ims: number;
  pus: number;
  recommendation_score: number;

  why_this_recipe?: string;
  explanation: string;
  explanation_data: ExplanationData;
  cuisine?: string | null;
  cuisine_confidence?: string | null;
  dietary_compatibility?: string | null;
  dietary_confidence?: string | null;
  estimated_time_minutes?: number | null;
  time_confidence?: string | null;
  preference_matches: Record<string, any>;
  preference_explanation?: string | null;
}

export interface PantryItem {
  id: string;
  name: string;
  normalized_name: string;
  category: string;
  quantity: number;
  unit: string;
  purchase_date?: string;
  expiry_date?: string;
  expiry_days: number;
  expiry_risk: 'high' | 'medium' | 'low';
  storage_location: 'fridge' | 'pantry' | 'freezer';
  status: 'available' | 'consumed' | 'expired';
}


