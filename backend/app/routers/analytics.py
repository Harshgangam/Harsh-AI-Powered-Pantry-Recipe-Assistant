from fastapi import APIRouter
from backend.app.services.analytics_service import SustainabilityAnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/sustainability")
def get_sustainability_analytics():
    """
    Returns high-level sustainability dashboard analytics:
    High-risk items rescued, food waste avoided (kg), pantry utilization %, and rescue trends.
    """
    return SustainabilityAnalyticsService.get_sustainability_metrics()
