from typing import Dict, Any, List
from backend.app.pantry.pantry_store import pantry_store


class SustainabilityAnalyticsService:
    @staticmethod
    def get_sustainability_metrics() -> Dict[str, Any]:
        pantry_items = pantry_store.get_all(status=None)
        available_items = [item for item in pantry_items if item.status == "available"]
        consumed_items = [item for item in pantry_items if item.status == "consumed"]
        high_risk_items = [item for item in available_items if item.expiry_risk == "high"]

        total_items_tracked = len(pantry_items)
        consumed_count = len(consumed_items)
        utilization_rate = (consumed_count / total_items_tracked * 100.0) if total_items_tracked > 0 else 78.5

        # Base mock analytics enriched with live pantry stats
        rescued_high_risk = max(14, consumed_count * 2)
        waste_avoided_kg = round(rescued_high_risk * 0.35, 2)

        trend_data = [
            {"day": "Mon", "rescued_items": 2, "utilization_pct": 72.0},
            {"day": "Tue", "rescued_items": 3, "utilization_pct": 75.5},
            {"day": "Wed", "rescued_items": 1, "utilization_pct": 78.0},
            {"day": "Thu", "rescued_items": 4, "utilization_pct": 81.2},
            {"day": "Fri", "rescued_items": 2, "utilization_pct": 82.0},
            {"day": "Sat", "rescued_items": 5, "utilization_pct": 86.4},
            {"day": "Sun", "rescued_items": 3, "utilization_pct": 88.5},
        ]

        return {
            "high_risk_rescued_count": rescued_high_risk,
            "pantry_utilization_rate": round(utilization_rate, 1),
            "estimated_food_waste_avoided_kg": waste_avoided_kg,
            "recipes_prepared_count": max(9, consumed_count),
            "current_high_risk_pantry_count": len(high_risk_items),
            "active_pantry_count": len(available_items),
            "sustainability_trend": trend_data,
            "status_summary": f"Great job! You have rescued {rescued_high_risk} high-risk ingredients and avoided {waste_avoided_kg} kg of household food waste this month."
        }
