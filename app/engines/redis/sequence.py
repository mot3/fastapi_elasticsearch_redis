from app.engines.redis.client import redis
from app.engines.logging import get_logger

logger = get_logger(__name__)

class SequenceService:
    def __init__(self, sequence_key: str):
        self.sequence_key = sequence_key
        self.logger = get_logger(f"SequenceService.{sequence_key}")

    async def get_next_id(self) -> int:
        """Get the next ID in the sequence"""
        try:
            next_id = await redis.incr(self.sequence_key)
            self.logger.info(f"Generated next ID: {next_id}")
            return next_id
        except Exception as e:
            self.logger.error(f"Failed to generate next ID", exc_info=True)
            raise ValueError(f"Failed to generate next ID: {str(e)}")

    async def get_current_id(self) -> int:
        """Get the current ID without incrementing"""
        try:
            current = await redis.get(self.sequence_key)
            return int(current) if current else 0
        except Exception as e:
            self.logger.error(f"Failed to get current ID", exc_info=True)
            raise ValueError(f"Failed to get current ID: {str(e)}")

    async def set_current_id(self, value: int) -> None:
        """Set the current ID value"""
        try:
            await redis.set(self.sequence_key, value)
            self.logger.info(f"Set current ID to: {value}")
        except Exception as e:
            self.logger.error(f"Failed to set current ID", exc_info=True)
            raise ValueError(f"Failed to set current ID: {str(e)}")

    async def reset(self) -> None:
        """Reset the sequence to 0"""
        try:
            await redis.delete(self.sequence_key)
            self.logger.info("Sequence reset to 0")
        except Exception as e:
            self.logger.error(f"Failed to reset sequence", exc_info=True)
            raise ValueError(f"Failed to reset sequence: {str(e)}") 