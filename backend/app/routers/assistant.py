from fastapi import APIRouter, HTTPException, status
from backend.app.assistant.models import (
    AssistantRequest,
    AssistantResponse,
    AssistantStatusResponse,
)
from backend.app.assistant.service import assistant_service

router = APIRouter(
    prefix="/assistant",
    tags=["assistant"],
)


@router.post(
    "/ask",
    response_model=AssistantResponse,
    status_code=status.HTTP_200_OK,
    summary="Get grounded recipe guidance from the AI assistant",
    description=(
        "Provides Entity-Grounded recipe assistance based strictly on authoritative recipe context, "
        "pantry match alignment, and curated substitutions. Supports explanation, step simplification, "
        "pantry preparation guidance, and grounded Q&A."
    ),
)
def ask_assistant(request: AssistantRequest) -> AssistantResponse:
    try:
        return assistant_service.get_guidance(request)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating assistant guidance: {str(e)}",
        )


@router.get(
    "/status",
    response_model=AssistantStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get AI assistant provider status",
    description="Returns current provider, model, and offline mock fallback status.",
)
def get_assistant_status() -> AssistantStatusResponse:
    try:
        return assistant_service.get_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking assistant status: {str(e)}",
        )
