import os
from redis.asyncio import Redis
from app.engines.logging import get_logger

logger = get_logger(__name__)

logger.info("Initializing Redis client")
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", "6379"))
redis_password = os.getenv("REDIS_PASSWORD", None)

redis = Redis(
    host=redis_host,
    port=redis_port,
    # password=redis_password,
    decode_responses=True
) 