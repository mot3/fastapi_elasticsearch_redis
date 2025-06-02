from fastapi import APIRouter
from app.api import v1

# Create the main API router
router = APIRouter(prefix="/api")

# Include versioned routers
router.include_router(v1.router)

__all__ = ["router"] 