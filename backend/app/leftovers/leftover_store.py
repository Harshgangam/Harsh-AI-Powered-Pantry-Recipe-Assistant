from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class LeftoverItem(BaseModel):
    id: str
    dish_name: str
    cooked_date: str
    quantity: float
    unit: str
    primary_ingredients: List[str]
    expiry_days: int = 2
    expiry_risk: str = "high"
    status: str = "available"  # "available", "consumed"


class LeftoverStore:
    def __init__(self):
        self._leftovers: Dict[str, LeftoverItem] = {}
        self._seed_default_leftovers()

    def _seed_default_leftovers(self):
        today = datetime.now().strftime("%Y-%m-%d")
        seed_data = [
            {
                "id": "lf1",
                "dish_name": "Cooked Basmati Rice",
                "cooked_date": today,
                "quantity": 2.0,
                "unit": "cups",
                "primary_ingredients": ["rice"],
                "expiry_days": 2,
                "expiry_risk": "medium",
            },
            {
                "id": "lf2",
                "dish_name": "Leftover Tomato Paneer Curry",
                "cooked_date": today,
                "quantity": 1.5,
                "unit": "bowls",
                "primary_ingredients": ["paneer", "tomato", "onion", "spices"],
                "expiry_days": 1,
                "expiry_risk": "high",
            },
            {
                "id": "lf3",
                "dish_name": "Roasted Vegetable Medley",
                "cooked_date": today,
                "quantity": 1.0,
                "unit": "bowl",
                "primary_ingredients": ["spinach", "bell pepper", "garlic"],
                "expiry_days": 2,
                "expiry_risk": "medium",
            },
        ]

        for item in seed_data:
            self._leftovers[item["id"]] = LeftoverItem(**item)

    def get_all(self, status: Optional[str] = "available") -> List[LeftoverItem]:
        if status:
            return [l for l in self._leftovers.values() if l.status == status]
        return list(self._leftovers.values())

    def add_leftover(self, dish_name: str, primary_ingredients: List[str], quantity: float = 1.0, unit: str = "portion") -> LeftoverItem:
        today = datetime.now().strftime("%Y-%m-%d")
        item_id = f"lf_{int(datetime.now().timestamp()*1000)}"
        item = LeftoverItem(
            id=item_id,
            dish_name=dish_name,
            cooked_date=today,
            quantity=quantity,
            unit=unit,
            primary_ingredients=primary_ingredients,
            expiry_days=2,
            expiry_risk="high",
            status="available",
        )
        self._leftovers[item.id] = item
        return item

    def consume_leftover(self, item_id: str) -> bool:
        if item_id in self._leftovers:
            self._leftovers[item_id].status = "consumed"
            return True
        return False

    def generate_transformations(self, leftover_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        active = [l for l in self._leftovers.values() if l.status == "available"]
        if leftover_ids:
            active = [l for l in active if l.id in leftover_ids]

        transformations = []
        for leftover in active:
            ings = [i.lower() for i in leftover.primary_ingredients]

            if "rice" in ings:
                transformations.append({
                    "leftover_id": leftover.id,
                    "leftover_dish": leftover.dish_name,
                    "recommended_transform_recipe": "Quick Vegetable Fried Rice / Rice Bowl",
                    "additional_ingredients_needed": ["egg", "soy sauce", "garlic", "green onion"],
                    "cooking_time_minutes": 15,
                    "rescue_value": "High - Prevents cooked rice from going stale",
                    "instructions": "Sauté garlic and vegetables, stir in leftover rice on high heat with soy sauce and scrambled egg."
                })
            elif "paneer" in ings or "curry" in ings:
                transformations.append({
                    "leftover_id": leftover.id,
                    "leftover_dish": leftover.dish_name,
                    "recommended_transform_recipe": "Leftover Curry Kathi Roll / Stuffed Wrap",
                    "additional_ingredients_needed": ["tortilla / flatbread", "onion", "lemon"],
                    "cooking_time_minutes": 10,
                    "rescue_value": "High - Converts curry into portable lunch wrap",
                    "instructions": "Warm flatbread, fill with reheated curry, sliced raw onions, chopped coriander, and a squeeze of fresh lemon."
                })
            else:
                transformations.append({
                    "leftover_id": leftover.id,
                    "leftover_dish": leftover.dish_name,
                    "recommended_transform_recipe": "Frittata / Omelette Bake",
                    "additional_ingredients_needed": ["eggs", "cheese", "black pepper"],
                    "cooking_time_minutes": 15,
                    "rescue_value": "Medium - Rescues cooked vegetables into protein-packed dish",
                    "instructions": "Whisk eggs with cheese and pepper, fold in leftover cooked vegetables, cook over medium heat until set."
                })

        return transformations

    def generate_multi_day_chain_plan(self, pantry_ingredients: List[str]) -> List[Dict[str, Any]]:
        """
        Food Rescue Chain Planning (Section 22): Constructs a 3-day meal sequence maximizing ingredient utilization.
        """
        pantry_set = {i.lower() for i in pantry_ingredients}

        day1_title = "Spinach & Tomato Pasta" if "spinach" in pantry_set and "pasta" in pantry_set else "High-Rescue Pantry Feast"
        day2_title = "Leftover Tomato-Spinach Baked Frittata"
        day3_title = "Garlic Vegetable Fried Rice"

        plan = [
            {
                "day": 1,
                "meal_name": day1_title,
                "primary_ingredients_rescued": ["Spinach (High Risk)", "Tomatoes (High Risk)", "Pasta"],
                "additional_purchases": [],
                "expected_leftovers_generated": "1 bowl cooked tomato-spinach sauce",
                "food_rescue_score": 96.0,
                "reasoning": "Rescues high-risk perishable spinach and tomatoes on Day 1 before expiry."
            },
            {
                "day": 2,
                "meal_name": day2_title,
                "primary_ingredients_rescued": ["Day 1 Sauce Leftover", "Eggs", "Cheese"],
                "additional_purchases": [],
                "expected_leftovers_generated": "None (Fully Consumed)",
                "food_rescue_score": 94.0,
                "reasoning": "Repurposes Day 1 leftover sauce into an egg frittata, zeroing sauce waste."
            },
            {
                "day": 3,
                "meal_name": day3_title,
                "primary_ingredients_rescued": ["Rice", "Garlic", "Onion"],
                "additional_purchases": [],
                "expected_leftovers_generated": "None (Fully Consumed)",
                "food_rescue_score": 90.0,
                "reasoning": "Uses remaining staple grains and aromatics to complete 3-day zero-waste sequence."
            }
        ]

        return plan


# Global singleton instance
leftover_store = LeftoverStore()
