import { RecipeRecommendationItem, PantryItem } from './recipe';

export interface PantryRequest {
  pantry_ingredients: string[];
  limit?: number;
  cuisine?: string | null;
  dietary_preference?: string | null;
  max_cooking_time_minutes?: number | null;
  rescue_mode?: boolean;
  pantry_items_details?: Partial<PantryItem>[];
}

export interface RecommendationResponse {
  normalized_pantry: string[];
  relevant_pantry: string[];
  total_candidates_evaluated: number;
  rescue_mode?: boolean;
  applied_preferences: {
    cuisine?: string | null;
    dietary_preference?: string | null;
    max_cooking_time_minutes?: number | null;
    rescue_mode?: boolean;
  };
  recommendations: RecipeRecommendationItem[];
}

export interface FoodRescueSimulationResponse {
  recipe_id: number;
  recipe_title: string;
  ingredients_consumed: string[];
  remaining_pantry: string[];
  high_risk_rescued_count: number;
  pantry_utilization_pct: number;
  missing_essential: string[];
  missing_optional: string[];
  can_prepare: boolean;
  simulation_summary: string;
}

export interface SustainabilityMetricsResponse {
  high_risk_rescued_count: number;
  pantry_utilization_rate: number;
  estimated_food_waste_avoided_kg: number;
  recipes_prepared_count: number;
  current_high_risk_pantry_count: number;
  active_pantry_count: number;
  sustainability_trend: Array<{ day: string; rescued_items: number; utilization_pct: number }>;
  status_summary: string;
}

export interface MealChainPlanResponse {
  plan: Array<{
    day: number;
    meal_name: string;
    primary_ingredients_rescued: string[];
    additional_purchases: string[];
    expected_leftovers_generated: string;
    food_rescue_score: number;
    reasoning: string;
  }>;
  total_rescue_score: number;
  estimated_waste_reduction: string;
}

export interface HealthResponse {
  status: string;
  data_ready: {
    recipes_parquet: boolean;
    ingredient_index_sqlite: boolean;
  };
}

export type AssistantTask = 'explain' | 'simplify' | 'guidance' | 'question';

export interface GroundingCitation {
  source_type: string;
  detail: string;
}

export interface AssistantRequest {
  recipe_id: number;
  task: AssistantTask;
  question?: string | null;
  pantry_ingredients?: string[];
  cuisine?: string | null;
  dietary_preference?: string | null;
  max_cooking_time_minutes?: number | null;
}

export interface AssistantResponse {
  recipe_id: number;
  recipe_title: string;
  task: AssistantTask;
  answer: string;
  citations: GroundingCitation[];
  substitutions_used: string[];
  unsupported_inquiries: string[];
  provider: string;
  model: string;
  is_mock: boolean;
}

export interface AssistantStatusResponse {
  status: string;
  provider: string;
  model: string;
  is_mock: boolean;
  has_api_key: boolean;
}
