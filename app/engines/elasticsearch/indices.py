from elasticsearch.exceptions import RequestError
from app.engines.elasticsearch.client import es
from app.engines.elasticsearch.mappings import INDEX_MAPPINGS
from app.engines.logging import get_logger, log_function_call

logger = get_logger(__name__)

@log_function_call
async def create_indices():
    """
    Create all required Elasticsearch indices if they don't exist.
    This function should be called during application startup.
    """
    for index_name, mapping in INDEX_MAPPINGS.items():
        try:
            exists = await es.indices.exists(index=index_name)
            if not exists:
                logger.info("Creating index", extra={
                    "extra_data": {
                        "index_name": index_name,
                        "mapping": mapping
                    }
                })
                await es.indices.create(index=index_name, body=mapping)
                logger.info("Index created successfully", extra={
                    "extra_data": {"index_name": index_name}
                })
            else:
                logger.info("Index already exists", extra={
                    "extra_data": {"index_name": index_name}
                })
        except RequestError as e:
            logger.error("Error creating index", exc_info=True, extra={
                "extra_data": {
                    "index_name": index_name,
                    "error_type": "RequestError",
                    "error_details": str(e)
                }
            })
            raise
        except Exception as e:
            logger.error("Unexpected error creating index", exc_info=True, extra={
                "extra_data": {
                    "index_name": index_name,
                    "error_type": type(e).__name__,
                    "error_details": str(e)
                }
            })
            raise

@log_function_call
async def delete_indices():
    """
    Delete all indices. Use with caution!
    This function should only be used in development/testing environments.
    """
    for index_name in INDEX_MAPPINGS.keys():
        try:
            exists = await es.indices.exists(index=index_name)
            if exists:
                logger.warning("Deleting index", extra={
                    "extra_data": {"index_name": index_name}
                })
                await es.indices.delete(index=index_name)
                logger.info("Index deleted successfully", extra={
                    "extra_data": {"index_name": index_name}
                })
        except Exception as e:
            logger.error("Error deleting index", exc_info=True, extra={
                "extra_data": {
                    "index_name": index_name,
                    "error_type": type(e).__name__,
                    "error_details": str(e)
                }
            })
            raise

@log_function_call
async def recreate_indices():
    """
    Delete and recreate all indices. Use with caution!
    This function should only be used in development/testing environments.
    """
    logger.warning("Recreating all indices")
    await delete_indices()
    await create_indices()
    logger.info("All indices recreated successfully")

@log_function_call
async def get_indices_status():
    """
    Get the status of all indices.
    Returns a dictionary with index names and their existence status.
    """
    status = {}
    for index_name in INDEX_MAPPINGS.keys():
        try:
            exists = await es.indices.exists(index=index_name)
            if exists:
                # Get additional index information
                stats = await es.indices.stats(index=index_name)
                status_info = {
                    "exists": True,
                    "docs_count": stats["indices"][index_name]["total"]["docs"]["count"],
                    "size_in_bytes": stats["indices"][index_name]["total"]["store"]["size_in_bytes"]
                }
                logger.debug("Index status retrieved", extra={
                    "extra_data": {
                        "index_name": index_name,
                        "status": status_info
                    }
                })
                status[index_name] = status_info
            else:
                status[index_name] = {"exists": False}
                logger.debug("Index does not exist", extra={
                    "extra_data": {"index_name": index_name}
                })
        except Exception as e:
            error_info = {"exists": False, "error": str(e)}
            status[index_name] = error_info
            logger.error("Error getting index status", exc_info=True, extra={
                "extra_data": {
                    "index_name": index_name,
                    "error_type": type(e).__name__,
                    "error_details": str(e)
                }
            })
    
    return status