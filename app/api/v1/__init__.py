from fastapi import APIRouter
from app.api.v1 import products

# Create the v1 router
router = APIRouter(prefix="/v1")
# router = APIRouter()

# Include all route modules
router.include_router(products.router)

