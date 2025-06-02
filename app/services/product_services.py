from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from app.crud_base import CRUDBase
from app.engines.elasticsearch.client import es
from app.engines.logging import get_logger
from app.engines.redis.sequence import SequenceService
from elasticsearch import NotFoundError

class ProductService:
    def __init__(self):
        self.logger = get_logger("ProductService")
        self.crud = CRUDBase(index="products", id_field="product_uuid")
        self.sequence_service = SequenceService("product_id_seq")

    async def create_product(self, data: dict) -> dict:
        self.logger.info(f"Creating product with data: {data}")
        
        # Generate incremental product_id
        product_id = await self.sequence_service.get_next_id()
        data["product_id"] = product_id
        
        product = await self.crud.create(data)
        self.logger.info(f"Product created: {product.get('product_uuid')}")
      
        return product

    async def update_product(self, product_uuid: str, data: dict) -> dict:
        self.logger.info(f"Updating product {product_uuid} with data: {data}")
        
        # Don't allow updating product_id
        if "product_id" in data:
            del data["product_id"]
            
        product = await self.crud.update(product_uuid, data)
        self.logger.info(f"Product updated: {product_uuid}")
      
        return product

    async def delete_product(self, product_uuid: str) -> dict:
        self.logger.info(f"Deleting product: {product_uuid}")
        result = await self.crud.delete(product_uuid)
        self.logger.info(f"Product deleted from main index: {product_uuid}")
       
        return result

class ProductQueryService:
    def __init__(self):
        self.logger = get_logger("ProductQueryService")
        self.crud = CRUDBase(index="products", id_field="product_uuid")

    async def search(self, filters: dict, page: int = 1, size: int = 10, sort_by: Optional[str] = None) -> dict:
        """
        Search for products with filters and sorting.
        """
        query = self.prepare_query(filters)
        sort = self.prepare_sort(sort_by)
        
        try:
            response = await es.search(
                index="products",
                body={
                    "query": query,
                    "sort": sort
                },
                from_=(page - 1) * size,
                size=size
            )
            hits = response["hits"]["hits"]
            total = response["hits"]["total"]["value"]
            items = [hit["_source"] for hit in hits]
            return {
                "total": total,
                "page": page,
                "size": size,
                "items": items
            }
        except Exception as e:
            self.logger.error("Search failed", exc_info=True)
            raise HTTPException(status_code=400, detail=str(e))

    def prepare_query(self, filters: dict) -> dict:
        must = []
        filter_terms = []
        
        # Text search
        if "q" in filters:
            must.append({
                "multi_match": {
                    "query": filters["q"],
                    "fields": ["name^3", "brand^2"]
                }
            })
        
        # Exact matches
        for field in ["category", "brand"]:
            if field in filters:
                filter_terms.append({"term": {field: filters[field]}})
        
        # Price range
        if "min_price" in filters or "max_price" in filters:
            range_query = {"range": {"price": {}}}
            if "min_price" in filters:
                range_query["range"]["price"]["gte"] = filters["min_price"]
            if "max_price" in filters:
                range_query["range"]["price"]["lte"] = filters["max_price"]
            filter_terms.append(range_query)
        
        query = {"bool": {"must": must}}
        if filter_terms:
            query["bool"]["filter"] = filter_terms
        
        return query

    def prepare_sort(self, sort_by: Optional[str]) -> list:
        """
        Prepare sort criteria based on sort_by parameter.
        """
        if not sort_by:
            return [{"product_id": "desc"}]
        
        sort_map = {
            "price_asc": [{"price": "asc"}],
            "price_desc": [{"price": "desc"}],
            "newest": [{"created_at": "desc"}],
            "popularity": [{"_score": "desc"}]
        }
        
        return sort_map.get(sort_by, [{"product_id": "desc"}])
