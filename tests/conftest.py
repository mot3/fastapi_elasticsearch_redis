# from tests.test_settings import *  # This must be the first import
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import os
import asyncio
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator, NamedTuple
from datetime import datetime
from elasticsearch import AsyncElasticsearch, NotFoundError
from elasticsearch.exceptions import NotFoundError

# # Set default fixture loop scope
# pytest_plugins = ("pytest_asyncio",)
# pytestmark = @pytest.mark.asyncio

class MockMeta(NamedTuple):
    status: int
    headers: dict

# Create a mock Redis client
mock_redis = AsyncMock()
mock_redis.incr = AsyncMock(return_value=1)
mock_redis.get = AsyncMock(return_value="1")
mock_redis.set = AsyncMock(return_value=True)
mock_redis.delete = AsyncMock(return_value=True)

# Create a mock Elasticsearch client
mock_client = AsyncMock(spec=AsyncElasticsearch)

# Mock storage for documents
mock_storage = {}

# Mock index operations
async def mock_index(*args, **kwargs):
    index = args[0] if args else kwargs.get("index", "products")
    doc_id = kwargs.get("id", "test_id")
    document = kwargs.get("document", {})
    mock_storage[doc_id] = document
    return {
        "_id": doc_id,
        "_index": index,
        "result": "created",
        "_version": 1,
        "_shards": {"total": 1, "successful": 1, "failed": 0},
        "_seq_no": 0,
        "_primary_term": 1
    }

async def mock_get(*args, **kwargs):
    index = args[0] if args else kwargs.get("index", "products")
    doc_id = kwargs.get("id", "test_id")
    if doc_id not in mock_storage:
        error_meta = MockMeta(status=404, headers={})
        error_data = {
            "root_cause": [{"type": "document_missing_exception", "reason": f"Document {doc_id} not found"}],
            "type": "document_missing_exception",
            "reason": f"Document {doc_id} not found"
        }
        raise NotFoundError(message=f"Document {doc_id} not found", meta=error_meta, body=error_data)
    return {
        "_id": doc_id,
        "_index": index,
        "_version": 1,
        "found": True,
        "_source": mock_storage[doc_id]
    }

async def mock_update(*args, **kwargs):
    index = args[0] if args else kwargs.get("index", "products")
    doc_id = kwargs.get("id", "test_id")
    if doc_id not in mock_storage:
        error_meta = MockMeta(status=404, headers={})
        error_data = {
            "root_cause": [{"type": "document_missing_exception", "reason": f"Document {doc_id} not found"}],
            "type": "document_missing_exception",
            "reason": f"Document {doc_id} not found"
        }
        raise NotFoundError(message=f"Document {doc_id} not found", meta=error_meta, body=error_data)
    update_data = kwargs.get("doc", {})
    mock_storage[doc_id].update(update_data)
    return {
        "_id": doc_id,
        "_index": index,
        "result": "updated",
        "_version": 2,
        "_shards": {"total": 1, "successful": 1, "failed": 0},
        "_seq_no": 1,
        "_primary_term": 1
    }

async def mock_delete(*args, **kwargs):
    index = args[0] if args else kwargs.get("index", "products")
    doc_id = kwargs.get("id", "test_id")
    if doc_id not in mock_storage:
        error_meta = MockMeta(status=404, headers={})
        error_data = {
            "root_cause": [{"type": "document_missing_exception", "reason": f"Document {doc_id} not found"}],
            "type": "document_missing_exception",
            "reason": f"Document {doc_id} not found"
        }
        raise NotFoundError(message=f"Document {doc_id} not found", meta=error_meta, body=error_data)
    del mock_storage[doc_id]
    return {
        "_id": doc_id,
        "_index": index,
        "result": "deleted",
        "_version": 2,
        "_shards": {"total": 1, "successful": 1, "failed": 0},
        "_seq_no": 1,
        "_primary_term": 1
    }

async def mock_search(*args, **kwargs):
    index = args[0] if args else kwargs.get("index", "products")
    hits = []
    for doc_id, doc in mock_storage.items():
        hits.append({
            "_index": index,
            "_id": doc_id,
            "_score": 1.0,
            "_source": doc
        })
    return {
        "took": 1,
        "timed_out": False,
        "_shards": {"total": 1, "successful": 1, "skipped": 0, "failed": 0},
        "hits": {
            "total": {"value": len(hits), "relation": "eq"},
            "max_score": 1.0,
            "hits": hits
        }
    }

mock_client.index = mock_index
mock_client.get = mock_get
mock_client.update = mock_update
mock_client.delete = mock_delete
mock_client.search = mock_search

# Mock indices operations
mock_indices = AsyncMock()
mock_indices.exists = AsyncMock(return_value=True)
mock_indices.create = AsyncMock(return_value={"acknowledged": True})
mock_indices.delete = AsyncMock(return_value={"acknowledged": True})
mock_indices.refresh = AsyncMock(return_value={"acknowledged": True})
mock_client.indices = mock_indices

# Mock transport layer
mock_transport = MagicMock()
mock_transport.perform_request = AsyncMock()
mock_client.transport = mock_transport

# Apply the patches
patch('elasticsearch.AsyncElasticsearch', return_value=mock_client).start()
patch('app.engines.elasticsearch.client.es', mock_client).start()
patch('app.engines.elasticsearch.indices.es', mock_client).start()
patch('app.engines.redis.client.redis', mock_redis).start()

# Now we can safely import FastAPI app
from app.main import app

@pytest_asyncio.fixture
async def mock_es():
    """Return the mock Elasticsearch client"""
    # Clear mock storage before each test
    mock_storage.clear()
    return mock_client

@pytest_asyncio.fixture
async def async_client(mock_es) -> AsyncGenerator[AsyncClient, None]:
    """
    Async test client fixture for FastAPI application
    """
    async with AsyncClient(transport=ASGITransport(app=app),
     base_url="http://test") as client:
        yield client

@pytest.fixture
def sample_product_data():
    """Sample product data for testing"""
    return {
        "product_uuid": "550e8400-e29b-41d4-a716-446655440000",
        "creator_id": "user123",
        "category": "electronics",
        "name": "Test Product",
        "brand": "TestBrand",
        "price": 999.99,
    }


@pytest.fixture
def test_product():
    """Sample product data fixture"""
    return {
        "product_uuid": "550e8400-e29b-41d4-a716-446655440001",
        "creator_id": "user123",
        "name": "Test Product",
        "price": 99.99,
        "category": "electronics",
        "brand": "TestBrand",
    }

@pytest.fixture
def test_products():
    """Sample products list fixture"""
    return [
        {
            "product_uuid": "550e8400-e29b-41d4-a716-446655440002",
            "creator_id": "user123",
            "name": "Product 1",
            "price": 99.99,
            "category": "electronics",
            "brand": "TestBrand",
        },
        {
            "product_uuid": "550e8400-e29b-41d4-a716-446655440003",
            "creator_id": "user124",
            "name": "Product 2",
            "price": 199.99,
            "category": "electronics",
            "brand": "TestBrand",
        }
    ]

@pytest_asyncio.fixture(autouse=True)
async def cleanup_indices(mock_es):
    """Clean up indices after each test"""
    mock_storage.clear()
    yield