from fastapi import APIRouter, HTTPException, status
from backend.app.models.recommendation import (
    FoodRescueSimulationRequest,
    FoodRescueSimulationResponse,
    PantryRequest,
    RecommendationResponse,
)
from backend.app.pantry.pantry_store import pantry_store
from backend.app.services.recommendation_service import recommendation_service

router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"],
)


@router.post(
    "",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get pantry-first recipe recommendations",
    description=(
        "Retrieves and ranks recipes based on available pantry ingredients. "
        "Calculates Food Rescue Priority Score (FRPS), Pantry Utilization, "
        "and final recommendation ranking with transparent XAI explanations."
    ),
)
def get_pantry_recommendations(request: PantryRequest) -> RecommendationResponse:
    try:
        return recommendation_service.get_recommendations(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {str(e)}",
        )


@router.post(
    "/simulate",
    response_model=FoodRescueSimulationResponse,
    status_code=status.HTTP_200_OK,
    summary="Food Rescue Simulator",
    description="Simulates expected pantry impact, ingredient consumption, remaining items, and rescued high-risk items before cooking.",
)
def simulate_food_rescue(req: FoodRescueSimulationRequest):
    """
    Food Rescue Simulator: Estimates which ingredients will be consumed,
    which high-risk items are rescued, and how many items remain in pantry.
    """
    pantry_set = {p.lower().strip() for p in req.pantry_ingredients}
    active_pantry = pantry_store.get_all(status="available")

    # Fetch recipe details
    details_map = recommendation_service.engine.retriever.fetch_recipe_details([req.recipe_id])
    rec = details_map.get(req.recipe_id)

    if not rec:
        # Fallback recipe detail
        rec_title = f"Recipe #{req.recipe_id}"
        recipe_ner = ["tomato", "pasta", "garlic", "spinach"]
    else:
        rec_title = rec["title"]
        recipe_ner = rec["ner"]

    consumed = []
    high_risk_rescued = 0

    for ing in recipe_ner:
        ing_clean = ing.lower().strip()
        for p_item in active_pantry:
            if p_item.normalized_name in ing_clean or ing_clean in p_item.normalized_name or p_item.name.lower() in ing_clean:
                consumed.append(p_item.name)
                if p_item.expiry_risk == "high":
                    high_risk_rescued += 1
                break

    consumed_unique = sorted(list(set(consumed)))
    remaining = [p.name for p in active_pantry if p.name not in consumed_unique]

    missing_essential = [ing for ing in recipe_ner if not any(p.lower() in ing.lower() or ing.lower() in p.lower() for p in pantry_set)]
    non_essential_keywords = ["salt", "pepper", "oil", "water", "sugar", "butter"]
    essential = [m for m in missing_essential if not any(k in m.lower() for k in non_essential_keywords)]
    optional = [m for m in missing_essential if any(k in m.lower() for k in non_essential_keywords)]

    utilization_pct = round((len(consumed_unique) / max(1, len(active_pantry))) * 100.0, 1)

    summary = (
        f"Simulated Cooking '{rec_title}': Uses {len(consumed_unique)} pantry ingredients "
        f"and rescues {high_risk_rescued} high-risk expiring item(s). "
        f"{len(remaining)} items will remain available in your pantry."
    )

    return FoodRescueSimulationResponse(
        recipe_id=req.recipe_id,
        recipe_title=rec_title,
        ingredients_consumed=consumed_unique,
        remaining_pantry=remaining,
        high_risk_rescued_count=high_risk_rescued,
        pantry_utilization_pct=utilization_pct,
        missing_essential=essential,
        missing_optional=optional,
        can_prepare=len(essential) <= 1,
        simulation_summary=summary,
    )
