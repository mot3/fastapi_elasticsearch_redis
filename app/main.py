from fastapi import FastAPI
from dotenv import load_dotenv
import os
from app.api import router
from app.engines.elasticsearch.indices import create_indices
from app.engines.logging import setup_logging, get_logger
from app.engines.elasticsearch.client import es
from app.error_handlers import register_error_handlers
from contextlib import asynccontextmanager
from app.engines.redis.sequence_init import sequence_initializer

# Load environment variables
load_dotenv()

# Setup logging
setup_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    log_file=os.getenv("LOG_FILE", "app.log")
)
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application initialization")
    try:
        # Initialize Elasticsearch indices
        # await create_indices()
        logger.info("Elasticsearch indices initialized successfully")
        
        # Initialize Redis sequences from database
        await sequence_initializer.initialize_all_sequences()
        logger.info("Redis sequences initialized from database successfully")
        
    except Exception as e:
        logger.error("Failed to initialize application", exc_info=True)
        raise
    try:
        yield
    finally:
        logger.info("Shutting down application")
        try:
            await es.close()
            logger.info("Elasticsearch connection closed")
        except Exception as e:
            logger.error("Error during shutdown", exc_info=True)

app = FastAPI(
    title="Product Management API",
    description="RESTful API for managing products",
    version="1.0.0",
    openapi_tags=[
        {"name": "products", "description": "Operations with products"},
    ],
    lifespan=lifespan,
)

register_error_handlers(app)

# Include the API router
app.include_router(router)

@app.get("/")
async def root():
    logger.debug("Health check endpoint called")
    return {"message": "Product Management API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )