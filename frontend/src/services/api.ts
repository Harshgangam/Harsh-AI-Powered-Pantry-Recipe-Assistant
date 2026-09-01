import {
  AssistantRequest,
  AssistantResponse,
  AssistantStatusResponse,
  FoodRescueSimulationResponse,
  HealthResponse,
  MealChainPlanResponse,
  PantryRequest,
  RecommendationResponse,
  SustainabilityMetricsResponse,
} from '../types/api';
import { PantryItem, LeftoverItem } from '../types/recipe';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export class ApiServiceError extends Error {
  status?: number;
  details?: any;

  constructor(message: string, status?: number, details?: any) {
    super(message);
    this.name = 'ApiServiceError';
    this.status = status;
    this.details = details;
  }
}

export async function fetchRecommendations(
  request: PantryRequest
): Promise<RecommendationResponse> {
  try {
    const url = `${API_BASE}/api/recommendations`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      let errorMsg = `Server error (${response.status})`;
      let details: any = null;
      try {
        const errorData = await response.json();
        details = errorData;
        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            errorMsg = errorData.detail.map((e: any) => e.msg || e).join(', ');
          } else {
            errorMsg = String(errorData.detail);
          }
        }
      } catch {
        // Fall back
      }
      throw new ApiServiceError(errorMsg, response.status, details);
    }

    return (await response.json()) as RecommendationResponse;
  } catch (err: any) {
    if (err instanceof ApiServiceError) {
      throw err;
    }
    throw new ApiServiceError(
      'Unable to connect to the backend server. Please verify that the FastAPI backend is running.'
    );
  }
}

export async function simulateFoodRescue(
  recipeId: number,
  pantryIngredients: string[]
): Promise<FoodRescueSimulationResponse> {
  const url = `${API_BASE}/api/recommendations/simulate`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ recipe_id: recipeId, pantry_ingredients: pantryIngredients }),
  });
  if (!response.ok) throw new ApiServiceError(`Simulation failed (${response.status})`);
  return (await response.json()) as FoodRescueSimulationResponse;
}

export async function fetchPantryItems(): Promise<PantryItem[]> {
  try {
    const response = await fetch(`${API_BASE}/api/pantry/items`);
    if (!response.ok) return [];
    return (await response.json()) as PantryItem[];
  } catch {
    return [];
  }
}

export async function addPantryItem(item: { name: string; category?: string; quantity?: number; unit?: string; expiry_days?: number }): Promise<PantryItem> {
  const response = await fetch(`${API_BASE}/api/pantry/items`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(item),
  });
  return (await response.json()) as PantryItem;
}

export async function deletePantryItem(itemId: string): Promise<void> {
  await fetch(`${API_BASE}/api/pantry/items/${itemId}`, { method: 'DELETE' });
}

export async function cookRecipe(recipeId: number, title: string, ner: string[]): Promise<any> {
  const response = await fetch(`${API_BASE}/api/pantry/cook`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ recipe_id: recipeId, recipe_title: title, recipe_ner: ner }),
  });
  return await response.json();
}

export async function scanPantryImage(): Promise<any> {
  const response = await fetch(`${API_BASE}/api/pantry/scan-image`, { method: 'POST' });
  return await response.json();
}

export async function fetchLeftovers(): Promise<LeftoverItem[]> {
  try {
    const response = await fetch(`${API_BASE}/api/leftovers`);
    if (!response.ok) return [];
    return (await response.json()) as LeftoverItem[];
  } catch {
    return [];
  }
}

export async function addLeftover(dishName: string, primaryIngredients: string[]): Promise<LeftoverItem> {
  const response = await fetch(`${API_BASE}/api/leftovers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dish_name: dishName, primary_ingredients: primaryIngredients }),
  });
  return (await response.json()) as LeftoverItem;
}

export async function fetchMealChainPlan(pantryIngredients?: string[]): Promise<MealChainPlanResponse> {
  const response = await fetch(`${API_BASE}/api/leftovers/chain-plan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pantry_ingredients: pantryIngredients }),
  });
  return (await response.json()) as MealChainPlanResponse;
}

export async function fetchSustainabilityAnalytics(): Promise<SustainabilityMetricsResponse> {
  const response = await fetch(`${API_BASE}/api/analytics/sustainability`);
  return (await response.json()) as SustainabilityMetricsResponse;
}

export async function checkBackendHealth(): Promise<HealthResponse> {
  try {
    const response = await fetch(`${API_BASE}/health`, { method: 'GET' });
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }
    return (await response.json()) as HealthResponse;
  } catch {
    throw new ApiServiceError('Backend is currently offline or unreachable.');
  }
}

export async function askRecipeAssistant(
  request: AssistantRequest
): Promise<AssistantResponse> {
  const url = `${API_BASE}/api/assistant/ask`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new ApiServiceError(`Assistant error (${response.status})`);
  }

  return (await response.json()) as AssistantResponse;
}

export async function fetchAssistantStatus(): Promise<AssistantStatusResponse> {
  const url = `${API_BASE}/api/assistant/status`;
  const response = await fetch(url, { method: 'GET' });
  if (!response.ok) {
    throw new ApiServiceError(`Status check failed (${response.status})`);
  }
  return (await response.json()) as AssistantStatusResponse;
}
