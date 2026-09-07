from fastapi import APIRouter, HTTPException, status
from backend.app.models.recommendation import (
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
