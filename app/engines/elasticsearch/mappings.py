"""
Elasticsearch index mappings configuration
"""

PRODUCTS_MAPPING = {
    "mappings": {
        "properties": {
            "product_id": {"type": "long"},
            "product_uuid": {"type": "keyword"},
            "creator_id": {"type": "keyword"},
            "category": {"type": "keyword"},
            "name": {"type": "text"},
            "brand": {"type": "keyword"},
            "price": {"type": "double"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"}
        }
    }
}


# Dictionary mapping index names to their mappings
INDEX_MAPPINGS = {
    "": PRODUCTS_MAPPING,
} 