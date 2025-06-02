import pytest
from httpx import AsyncClient

# Remove the global pytestmark and use specific marks for each test
# @pytest.mark.asyncio
@pytest.mark.asyncio
async def test_create_product(async_client: AsyncClient, sample_product_data):
    """Test creating a new product"""
    response = await async_client.post("/api/v1/products/", json=sample_product_data)
    assert response.status_code == 200
    data = response.json()
    
    # Verify all required fields
    assert data["product_id"] > 0
    assert data["product_uuid"] == sample_product_data["product_uuid"]
    assert data["creator_id"] == sample_product_data["creator_id"]
    assert data["name"] == sample_product_data["name"]
    assert data["category"] == sample_product_data["category"]
    assert data["brand"] == sample_product_data["brand"]
    assert data["price"] == sample_product_data["price"]
    
    # Verify timestamps are present
    assert "created_at" in data
    assert "updated_at" in data

@pytest.mark.asyncio
async def test_get_product(async_client: AsyncClient, sample_product_data):
    """Test getting a product by ID"""
    # Create a product first
    create_response = await async_client.post("/api/v1/products/", json=sample_product_data)
    assert create_response.status_code == 200
    created_data = create_response.json()
    
    # Get the product
    get_response = await async_client.get(f"/api/v1/products/{created_data['product_uuid']}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    
    # Verify all fields match
    assert get_data["product_id"] == created_data["product_id"]
    assert get_data["product_uuid"] == created_data["product_uuid"]
    assert get_data["creator_id"] == created_data["creator_id"]
    assert get_data["name"] == created_data["name"]
    assert get_data["category"] == created_data["category"]

@pytest.mark.asyncio
async def test_update_product(
    async_client: AsyncClient, 
    sample_product_data):
    """Test updating a product"""
    # First create a product
    create_response = await async_client.post(
        "/api/v1/products/", json=sample_product_data)
    assert create_response.status_code == 200
    created_data = create_response.json()

    # Update the product
    update_data = {
        "name": "Updated Product Name",
        "price": 1099.99
    }
    update_response = await async_client.put(
        f"/api/v1/products/{created_data['product_uuid']}", 
        json=update_data)
    assert update_response.status_code == 200
    updated_data = update_response.json()
    
    # Verify updated fields
    assert updated_data["product_id"] == created_data["product_id"]
    assert updated_data["product_uuid"] == created_data["product_uuid"]
    assert updated_data["name"] == update_data["name"]
    assert updated_data["price"] == update_data["price"]
    assert updated_data["creator_id"] == created_data["creator_id"]

@pytest.mark.asyncio
async def test_delete_product(async_client: AsyncClient, sample_product_data):
    """Test deleting a product"""
    # First create a product
    create_response = await async_client.post("/api/v1/products/", json=sample_product_data)
    assert create_response.status_code == 200
    created_data = create_response.json()
    
    # Delete the product
    delete_response = await async_client.delete(f"/api/v1/products/{created_data['product_uuid']}")
    assert delete_response.status_code == 200
    
    # Verify product is deleted
    get_response = await async_client.get(f"/api/v1/products/{created_data['product_uuid']}")
    assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_search_products(async_client: AsyncClient, sample_product_data):
    """Test searching products"""
    # Create a product
    await async_client.post("/api/v1/products/", json=sample_product_data)
    
    # Search by various criteria
    search_params = {
        "q": sample_product_data["name"],
        "category": sample_product_data["category"],
        "min_price": sample_product_data["price"] - 100,
        "max_price": sample_product_data["price"] + 100,
        "page": 1,
        "page_size": 10
    }
    
    response = await async_client.get("/api/v1/products/", params=search_params)
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] > 0
    assert len(data["items"]) > 0
    assert data["page"] == search_params["page"]
    assert data["size"] == search_params["page_size"]
    
    # Verify first item matches our created product
    first_item = data["items"][0]
    assert first_item["product_uuid"] == sample_product_data["product_uuid"]
    assert first_item["name"] == sample_product_data["name"]
    assert first_item["category"] == sample_product_data["category"]

@pytest.mark.asyncio
async def test_invalid_product_creation(async_client: AsyncClient):
    """Test creating a product with invalid data"""
    invalid_data = {
        "name": "Invalid Product",
        # Missing required fields
    }
    response = await async_client.post("/api/v1/products/", json=invalid_data)
    assert response.status_code == 422  # Validation error

@pytest.mark.asyncio
async def test_invalid_price_update(async_client: AsyncClient, sample_product_data):
    """Test updating a product with invalid price"""
    # Create a product first
    create_response = await async_client.post("/api/v1/products/", json=sample_product_data)
    assert create_response.status_code == 200
    product_id = create_response.json()["product_id"]
    
    # Try to update with invalid price
    update_data = {"price": -100}  # Negative price should be invalid
    response = await async_client.put(f"/api/v1/products/{product_id}", json=update_data)
    assert response.status_code == 422  # Validation error

@pytest.mark.asyncio
async def test_product_not_found(async_client: AsyncClient):
    """Test operations on non-existent product"""
    non_existent_id = "non_existent_product_id"
    
    # Test get
    get_response = await async_client.get(f"/api/v1/products/{non_existent_id}")
    assert get_response.status_code == 404
    
    # Test update
    update_response = await async_client.put(
        f"/api/v1/products/{non_existent_id}",
        json={"name": "Updated Name"}
    )
    assert update_response.status_code == 404
    
    # Test delete
    delete_response = await async_client.delete(f"/api/v1/products/{non_existent_id}")
    assert delete_response.status_code == 404