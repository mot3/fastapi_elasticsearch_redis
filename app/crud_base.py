from datetime import datetime, timezone
from elasticsearch import NotFoundError
from fastapi import HTTPException, status
from app.engines.elasticsearch.client import es
from app.engines.logging import get_logger

class CRUDBase:
    def __init__(self, index: str, id_field: str = "id"):
        self.index = index
        self.id_field = id_field
        self.logger = get_logger(f"CRUDBase.{self.index}")

    async def create(self, data: dict):
        if "created_at" not in data:
            data["created_at"] = datetime.now(timezone.utc)
        if "updated_at" not in data:
            data["updated_at"] = datetime.now(timezone.utc)
        # Convert datetime objects to ISO strings
        data["created_at"] = data["created_at"].isoformat()
        data["updated_at"] = data["updated_at"].isoformat()
        try:
            self.logger.info(f"Creating document in {self.index}", extra={"extra_data": data})
            response = await es.index(
                index=self.index,
                id=data.get(self.id_field),
                document=data
            )
            await es.indices.refresh(index=self.index)
            self.logger.info(f"Document created in {self.index}", extra={"extra_data": {"id": response["_id"]}})
            return {"id": response["_id"], **data}
        except Exception as e:
            self.logger.error(f"Failed to create document in {self.index}", exc_info=True, extra={"extra_data": {"error": str(e)}})
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def update(self, id: str, data: dict):
        try:
            self.logger.info(f"Updating document {id} in {self.index}", extra={"extra_data": data})
            await es.get(index=self.index, id=id)
            update_data = {k: v for k, v in data.items() if v is not None}
            if "updated_at" not in update_data:
                update_data["updated_at"] = datetime.now(timezone.utc)
            response = await es.update(
                index=self.index,
                id=id,
                doc=update_data
            )
            await es.indices.refresh(index=self.index)
            updated_doc = await es.get(index=self.index, id=id)
            self.logger.info(f"Document {id} updated in {self.index}")
            return updated_doc["_source"]
        except NotFoundError:
            self.logger.warning(f"Document {id} not found for update in {self.index}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item not found in {self.index}")
        except Exception as e:
            self.logger.error(f"Failed to update document {id} in {self.index}", exc_info=True, extra={"extra_data": {"error": str(e)}})
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def delete(self, id: str):
        try:
            self.logger.info(f"Deleting document {id} from {self.index}")
            response = await es.delete(index=self.index, id=id)
            await es.indices.refresh(index=self.index)
            self.logger.info(f"Document {id} deleted from {self.index}")
            return {"message": f"Item deleted successfully from {self.index}"}
        except NotFoundError:
            self.logger.warning(f"Document {id} not found for deletion in {self.index}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item not found in {self.index}")
        except Exception as e:
            self.logger.error(f"Failed to delete document {id} from {self.index}", exc_info=True, extra={"extra_data": {"error": str(e)}})
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    async def get(self, id: str):
        try:
            self.logger.info(f"Getting document {id} from {self.index}")
            response = await es.get(index=self.index, id=id)
            self.logger.info(f"Document {id} fetched from {self.index}")
            return response["_source"]
        except NotFoundError:
            self.logger.warning(f"Document {id} not found in {self.index}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item not found in {self.index}")
        except Exception as e:
            self.logger.error(f"Failed to get document {id} from {self.index}", exc_info=True, extra={"extra_data": {"error": str(e)}})
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def exists(self, id: str) -> bool:
        try:
            self.logger.info(f"Checking if document {id} exists in {self.index}")
            await es.get(index=self.index, id=id)
            return True
        except NotFoundError:
            return False
        except Exception as e:
            self.logger.error(f"Failed to check document existence in {self.index}", exc_info=True, extra={"extra_data": {"error": str(e)}})
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def search(self, query: dict, page: int = 1, size: int = 10):
        try:
            self.logger.info(f"Searching documents in {self.index}", extra={"extra_data": {"query": query, "page": page, "size": size}})
            response = await es.search(
                index=self.index,
                body=query,
                from_=(page - 1) * size,
                size=size
            )
            hits = response["hits"]["hits"]
            total = response["hits"]["total"]["value"]
            items = [hit["_source"] for hit in hits]
            self.logger.info(f"Search completed in {self.index}", extra={"extra_data": {"count": len(items)}})
            return {
                "total": total,
                "page": page,
                "size": size,
                "items": items
            }
        except Exception as e:
            self.logger.error(f"Failed to search documents in {self.index}", exc_info=True, extra={"extra_data": {"error": str(e)}})
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))