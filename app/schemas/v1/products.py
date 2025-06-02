from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional
from datetime import datetime

class ProductBase(BaseModel):
    """Base product schema with all required fields"""
    product_uuid: str = Field(..., description="Unique UUID for the product")
    creator_id: str = Field(..., description="ID of the user who created the product")
    category: str = Field(..., description="Product category")
    name: str = Field(..., description="Product name")
    brand: str = Field(..., description="Product brand")
    price: float = Field(..., gt=0, description="Product price")

class ProductCreate(BaseModel):
    """Schema for creating a new product"""
    product_uuid: str = Field(..., description="Unique UUID for the product")
    creator_id: str = Field(..., description="ID of the user who created the product")
    category: str = Field(..., description="Product category")
    name: str = Field(..., description="Product name")
    brand: str = Field(..., description="Product brand")
    price: float = Field(..., gt=0, description="Product price")

class ProductUpdate(BaseModel):
    """Schema for updating an existing product"""
    category: Optional[str] = Field(None, description="Product category")
    name: Optional[str] = Field(None, description="Product name")
    brand: Optional[str] = Field(None, description="Product brand")
    model: Optional[str] = Field(None, description="Product model")
    price: Optional[float] = Field(None, gt=0, description="Product price")

class Product(BaseModel):
    """Complete product schema including timestamps"""
    product_id: int = Field(..., description="Auto-incremented product ID")
    product_uuid: str = Field(..., description="Unique UUID for the product")
    creator_id: str = Field(..., description="ID of the user who created the product")
    category: str = Field(..., description="Product category")
    name: str = Field(..., description="Product name")
    brand: str = Field(..., description="Product brand")
    price: float = Field(..., gt=0, description="Product price")
    created_at: datetime = Field(..., description="Timestamp when the product was created")
    updated_at: datetime = Field(..., description="Timestamp when the product was last updated")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "product_id": 123,
                "product_uuid": "550e8400-e29b-41d4-a716-446655440000",
                "creator_id": "user123",
                "category": "electronics",
                "name": "Smartphone X",
                "brand": "TechBrand",
                "price": 999.99,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    ) 