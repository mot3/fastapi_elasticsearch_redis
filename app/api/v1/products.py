from fastapi import APIRouter, Query
from typing import Optional
from app.schemas.v1.products import Product, ProductCreate, ProductUpdate
from app.services.product_services import ProductService, ProductQueryService

router = APIRouter(prefix="/products", tags=["products"])
product_service = ProductService()
product_query_service = ProductQueryService()

@router.post("/", response_model=Product)
async def create_product(product: ProductCreate):
    """
    Create a new product. Validates product data and syncs it with the Elasticsearch index.
    - **Request body:** ProductCreate schema (JSON)
    - **Returns:** The created product (Product schema)
    - **Errors:** 400 Bad Request if validation or sync fails
    """
    return await product_service.create_product(product.model_dump())

@router.put("/{product_uuid}", response_model=Product)
async def update_product(product_uuid: str, product: ProductUpdate):
    """
    Update an existing product. Validates and syncs to Elasticsearch.
    - **Path parameter:** product_uuid (str)
    - **Request body:** ProductUpdate schema (JSON)
    - **Returns:** The updated product (Product schema)
    - **Errors:** 400 Bad Request if validation or sync fails, 404 Not Found if product doesn't exist
    """
    return await product_service.update_product(product_uuid, product.model_dump(exclude_unset=True))

@router.delete("/{product_uuid}")
async def delete_product(product_uuid: str):
    """
    Delete a product by its UUID.
    - **Path parameter:** product_uuid (str)
    - **Returns:** Success message
    - **Errors:** 404 Not Found if the product does not exist
    """
    return await product_service.delete_product(product_uuid)

@router.get("/{product_uuid}", response_model=Product)
async def get_product(product_uuid: str):
    """
    Retrieve a product by its UUID.
    - **Path parameter:** product_uuid (str)
    - **Returns:** The requested product (Product schema)
    - **Errors:** 404 Not Found if the product does not exist
    """
    return await product_service.crud.get(product_uuid)

@router.get("/")
async def search_products(
    q: Optional[str] = Query(None, description="Search keyword"),
    category: Optional[str] = Query(None, description="Product category"),
    brand: Optional[str] = Query(None, description="Product brand"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    page: int = Query(1, gt=0, description="Page number (default 1)"),
    page_size: int = Query(10, gt=0, le=100, description="Items per page (default 10, max 100)"),
    sort_by: Optional[str] = Query(None, description="Sort by: price_asc, price_desc, newest, popularity")
):
    """
    Search products using keyword, filters, pagination, and sorting.
    - **Query parameters:**
        - q: str (search keyword)
        - category: str
        - brand: str
        - min_price: float
        - max_price: float
        - page: int (default 1)
        - size: int (default 10, max 100)
        - sort_by: str (price_asc, price_desc, newest, popularity)
    - **Returns:** Paginated search results with total, page, size, and items (list of Product)
    - **Errors:** 400 Bad Request if search fails
    """
    filters = {}
    if q: filters["q"] = q
    if category: filters["category"] = category
    if brand: filters["brand"] = brand
    if min_price is not None: filters["min_price"] = min_price
    if max_price is not None: filters["max_price"] = max_price
    return await product_query_service.search(filters, page, page_size, sort_by)