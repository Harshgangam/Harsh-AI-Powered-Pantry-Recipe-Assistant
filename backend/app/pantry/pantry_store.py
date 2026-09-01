import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PantryItem(BaseModel):
    id: str
    name: str
    normalized_name: str
    category: str = "General"
    quantity: float = 1.0
    unit: str = "pcs"
    purchase_date: Optional[str] = None
    expiry_date: Optional[str] = None
    expiry_days: int = 7
    expiry_risk: str = "low"  # "high", "medium", "low"
    storage_location: str = "pantry"  # "fridge", "pantry", "freezer"
    status: str = "available"  # "available", "consumed", "expired"


class PantryStore:
    def __init__(self):
        self._items: Dict[str, PantryItem] = {}
        self._seed_default_items()

    def _seed_default_items(self):
        today = datetime.now()
        seed_data = [
            {"id": "p1", "name": "Tomatoes", "category": "Produce", "quantity": 4.0, "unit": "pcs", "expiry_days": 2, "expiry_risk": "high", "storage_location": "fridge"},
            {"id": "p2", "name": "Fresh Spinach", "category": "Produce", "quantity": 200.0, "unit": "g", "expiry_days": 1, "expiry_risk": "high", "storage_location": "fridge"},
            {"id": "p3", "name": "Milk", "category": "Dairy", "quantity": 1.0, "unit": "liter", "expiry_days": 2, "expiry_risk": "high", "storage_location": "fridge"},
            {"id": "p4", "name": "Paneer", "category": "Dairy", "quantity": 250.0, "unit": "g", "expiry_days": 4, "expiry_risk": "medium", "storage_location": "fridge"},
            {"id": "p5", "name": "Eggs", "category": "Dairy", "quantity": 6.0, "unit": "pcs", "expiry_days": 5, "expiry_risk": "medium", "storage_location": "fridge"},
            {"id": "p6", "name": "Pasta", "category": "Grains", "quantity": 500.0, "unit": "g", "expiry_days": 30, "expiry_risk": "low", "storage_location": "pantry"},
            {"id": "p7", "name": "Rice", "category": "Grains", "quantity": 1000.0, "unit": "g", "expiry_days": 60, "expiry_risk": "low", "storage_location": "pantry"},
            {"id": "p8", "name": "Garlic", "category": "Produce", "quantity": 1.0, "unit": "bulb", "expiry_days": 14, "expiry_risk": "low", "storage_location": "pantry"},
            {"id": "p9", "name": "Onion", "category": "Produce", "quantity": 3.0, "unit": "pcs", "expiry_days": 10, "expiry_risk": "low", "storage_location": "pantry"},
            {"id": "p10", "name": "Olive Oil", "category": "Pantry", "quantity": 500.0, "unit": "ml", "expiry_days": 90, "expiry_risk": "low", "storage_location": "pantry"},
            {"id": "p11", "name": "Chicken Breast", "category": "Meat", "quantity": 500.0, "unit": "g", "expiry_days": 1, "expiry_risk": "high", "storage_location": "fridge"},
            {"id": "p12", "name": "Cheddar Cheese", "category": "Dairy", "quantity": 200.0, "unit": "g", "expiry_days": 6, "expiry_risk": "medium", "storage_location": "fridge"},
        ]

        for data in seed_data:
            days = data["expiry_days"]
            exp_date = (today + timedelta(days=days)).strftime("%Y-%m-%d")
            pur_date = (today - timedelta(days=2)).strftime("%Y-%m-%d")
            norm_name = data["name"].lower().replace("fresh ", "").replace("cheddar ", "").replace("breast", "").strip()

            item = PantryItem(
                id=data["id"],
                name=data["name"],
                normalized_name=norm_name,
                category=data["category"],
                quantity=data["quantity"],
                unit=data["unit"],
                purchase_date=pur_date,
                expiry_date=exp_date,
                expiry_days=days,
                expiry_risk=data["expiry_risk"],
                storage_location=data["storage_location"],
                status="available",
            )
            self._items[item.id] = item

    def get_all(self, status: Optional[str] = "available") -> List[PantryItem]:
        if status:
            return [item for item in self._items.values() if item.status == status]
        return list(self._items.values())

    def get_item(self, item_id: str) -> Optional[PantryItem]:
        return self._items.get(item_id)

    def add_item(self, item_data: Dict[str, Any]) -> PantryItem:
        today = datetime.now()
        item_id = item_data.get("id") or f"p_{int(today.timestamp()*1000)}"
        name = item_data.get("name", "Unknown Item")
        norm_name = item_data.get("normalized_name") or name.lower().strip()
        expiry_days = item_data.get("expiry_days", 7)

        if expiry_days <= 2:
            risk = "high"
        elif expiry_days <= 6:
            risk = "medium"
        else:
            risk = "low"

        exp_date = (today + timedelta(days=expiry_days)).strftime("%Y-%m-%d")
        pur_date = today.strftime("%Y-%m-%d")

        item = PantryItem(
            id=item_id,
            name=name,
            normalized_name=norm_name,
            category=item_data.get("category", "General"),
            quantity=float(item_data.get("quantity", 1.0)),
            unit=item_data.get("unit", "pcs"),
            purchase_date=pur_date,
            expiry_date=exp_date,
            expiry_days=expiry_days,
            expiry_risk=item_data.get("expiry_risk", risk),
            storage_location=item_data.get("storage_location", "pantry"),
            status="available",
        )
        self._items[item.id] = item
        return item

    def update_item(self, item_id: str, updates: Dict[str, Any]) -> Optional[PantryItem]:
        item = self._items.get(item_id)
        if not item:
            return None

        updated_dict = item.model_dump()
        for k, v in updates.items():
            if v is not None:
                updated_dict[k] = v

        if "expiry_days" in updates:
            days = updates["expiry_days"]
            if days <= 2:
                updated_dict["expiry_risk"] = "high"
            elif days <= 6:
                updated_dict["expiry_risk"] = "medium"
            else:
                updated_dict["expiry_risk"] = "low"

        updated_item = PantryItem(**updated_dict)
        self._items[item_id] = updated_item
        return updated_item

    def delete_item(self, item_id: str) -> bool:
        if item_id in self._items:
            del self._items[item_id]
            return True
        return False

    def cook_recipe(self, recipe_ner: List[str]) -> List[str]:
        """
        Pantry Feedback Loop: deducts recipe ingredients from available pantry items.
        """
        consumed = []
        for ing in recipe_ner:
            ing_clean = ing.lower().strip()
            for item in self._items.values():
                if item.status == "available" and (item.normalized_name in ing_clean or ing_clean in item.normalized_name or item.name.lower() in ing_clean):
                    item.quantity = max(0.0, item.quantity - 1.0)
                    if item.quantity == 0:
                        item.status = "consumed"
                    consumed.append(item.name)
                    break
        return consumed


# Global singleton instance
pantry_store = PantryStore()
