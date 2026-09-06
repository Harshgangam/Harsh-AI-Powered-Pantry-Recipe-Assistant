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
        
        # Real-time Utilization Rate
        utilization_rate = (consumed_count / total_items_tracked * 100.0) if total_items_tracked > 0 else 0.0

        # Real-time items rescued
        # We assume each consumed item was "rescued" from being thrown away
        rescued_total = consumed_count
        waste_avoided_kg = round(rescued_total * 0.35, 2)  # Avg 0.35kg per item
        
        # Rough proxy for recipes prepared (assume ~2 tracked ingredients per recipe)
        recipes_prepared = rescued_total // 2

        # 7-day trend (Initialize with 0s for actual real-time display)
        # Since we don't track exact consumption date in MVP, we just show a static 
        # flatline until we add time-series tracking, but it will be REAL (0s) instead of fake mock data.
        trend_data = [
            {"day": "Mon", "rescued_items": 0, "utilization_pct": 0},
            {"day": "Tue", "rescued_items": 0, "utilization_pct": 0},
            {"day": "Wed", "rescued_items": 0, "utilization_pct": 0},
            {"day": "Thu", "rescued_items": 0, "utilization_pct": 0},
            {"day": "Fri", "rescued_items": 0, "utilization_pct": 0},
            {"day": "Sat", "rescued_items": 0, "utilization_pct": 0},
            {"day": "Sun", "rescued_items": rescued_total, "utilization_pct": round(utilization_rate, 1)}, # Put all current rescues on today
        ]

        if rescued_total == 0:
            status_msg = "Your pantry utilization journey starts here. Cook recipes to utilize items and track your impact!"
        else:
            status_msg = f"Great job! You have utilized {rescued_total} ingredients."

        return {
            "high_risk_rescued_count": rescued_total,
            "pantry_utilization_rate": round(utilization_rate, 1),
            "estimated_food_waste_avoided_kg": waste_avoided_kg,
            "recipes_prepared_count": recipes_prepared,
            "current_high_risk_pantry_count": len(high_risk_items),
            "active_pantry_count": len(available_items),
            "sustainability_trend": trend_data,
            "status_summary": status_msg
        }
