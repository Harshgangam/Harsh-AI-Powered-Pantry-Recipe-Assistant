from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.routers.recommendations import router as recommendations_router
from backend.app.routers.assistant import router as assistant_router
from backend.app.routers.pantry import router as pantry_router
from backend.app.routers.analytics import router as analytics_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Explainable RAG-Enhanced AI Pantry Intelligence & Food Rescue Assistant",
    version="1.0.0",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes at both /api and /api/v1 for clean access
app.include_router(recommendations_router, prefix="/api")
app.include_router(recommendations_router, prefix=settings.API_V1_STR)
app.include_router(assistant_router, prefix="/api")
app.include_router(assistant_router, prefix=settings.API_V1_STR)
app.include_router(pantry_router, prefix="/api")
app.include_router(pantry_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix="/api")
app.include_router(analytics_router, prefix=settings.API_V1_STR)


@app.get("/")
def read_root():
    return {
        "name": settings.PROJECT_NAME,
        "status": "online",
        "version": "1.0.0",
        "description": "RAG-Enhanced, Explainable Recipe Recommendation & Household Food-Waste Reduction System",
        "endpoints": {
            "pantry": "/api/pantry",
            "recommendations": "/api/recommendations",
            "assistant_ask": "/api/assistant/ask",
            "sustainability_analytics": "/api/analytics/sustainability",
            "health": "/health",
        },
    }

@app.get("/health")
def health_check():
    parquet_exists = settings.PARQUET_PATH.exists()
    sqlite_exists = settings.SQLITE_INDEX_PATH.exists()
    return {
        "status": "healthy",
        "data_ready": {
            "recipes_parquet": parquet_exists,
            "ingredient_index_sqlite": sqlite_exists,
        },
    }
