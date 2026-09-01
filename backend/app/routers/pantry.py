from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.app.pantry.pantry_store import PantryItem, pantry_store
from backend.app.models.recommendation import PantryCookRequest, PantryScanResponse

router = APIRouter(prefix="/pantry", tags=["pantry"])


class PantryItemCreate(BaseModel):
    name: str
    category: Optional[str] = "General"
    quantity: Optional[float] = 1.0
    unit: Optional[str] = "pcs"
    expiry_days: Optional[int] = 7
    storage_location: Optional[str] = "pantry"


class PantryItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    expiry_days: Optional[int] = None
    storage_location: Optional[str] = None
    status: Optional[str] = None


@router.get("", response_model=List[PantryItem])
@router.get("/items", response_model=List[PantryItem])
def get_pantry_items(status_filter: Optional[str] = "available"):
    """
    Get current user pantry items with expiry risk levels and status.
    """
    return pantry_store.get_all(status=status_filter)


@router.post("/items", response_model=PantryItem, status_code=status.HTTP_201_CREATED)
def add_pantry_item(item_data: PantryItemCreate):
    """
    Add a new ingredient item to the user's dynamic pantry inventory.
    """
    new_item = pantry_store.add_item(item_data.model_dump())
    return new_item


@router.put("/items/{item_id}", response_model=PantryItem)
def update_pantry_item(item_id: str, updates: PantryItemUpdate):
    """
    Update quantity, expiry, or details of a pantry item.
    """
    updated = pantry_store.update_item(item_id, updates.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Pantry item not found")
    return updated


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pantry_item(item_id: str):
    """
    Remove an ingredient from the user's pantry.
    """
    success = pantry_store.delete_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Pantry item not found")
    return None


@router.post("/cook")
def record_cooking_feedback(req: PantryCookRequest):
    """
    Pantry Feedback Loop: Updates the pantry database after the user cooks a recipe,
    deducting consumed quantities and marking depleted items as consumed.
    """
    consumed_items = pantry_store.cook_recipe(req.recipe_ner)
    return {
        "status": "success",
        "recipe_cooked": req.recipe_title,
        "ingredients_deducted": consumed_items,
        "message": f"Successfully updated pantry after cooking '{req.recipe_title}'. Deducted {len(consumed_items)} pantry ingredients.",
        "current_pantry_state": pantry_store.get_all(status="available"),
    }


@router.post("/scan-image", response_model=PantryScanResponse)
def scan_pantry_image():
    """
    Snap Your Pantry & OCR Expiry Detection: Simulates multi-modal computer vision
    object detection and OCR date extraction from a uploaded kitchen/fridge photo.
    """
    detected = [
        {"name": "Tomatoes", "category": "Produce", "quantity": 3.0, "unit": "pcs", "confidence": 0.94},
        {"name": "Milk Carton", "category": "Dairy", "quantity": 1.0, "unit": "liter", "confidence": 0.91},
        {"name": "Fresh Spinach", "category": "Produce", "quantity": 1.0, "unit": "pack", "confidence": 0.88},
        {"name": "Cheddar Cheese", "category": "Dairy", "quantity": 200.0, "unit": "g", "confidence": 0.85},
    ]

    dates = [
        {"item": "Milk Carton", "ocr_expiry_date": "2026-09-03", "expiry_days": 2, "confidence": "high"},
        {"item": "Cheddar Cheese", "ocr_expiry_date": "2026-09-07", "expiry_days": 6, "confidence": "medium"},
    ]

    # Automatically seed into pantry store
    for item in detected:
        pantry_store.add_item({
            "name": item["name"],
            "category": item["category"],
            "quantity": item["quantity"],
            "unit": item["unit"],
            "expiry_days": 2 if "Milk" in item["name"] else 4,
        })

    return PantryScanResponse(
        detected_ingredients=detected,
        ocr_extracted_dates=dates,
        scan_summary="Vision and OCR pipeline successfully identified 4 ingredients and 2 expiry dates from the image. Pantry items updated!",
    )
