from app.engines.elasticsearch.client import es
from app.engines.logging import get_logger
from app.engines.redis.sequence import SequenceService

logger = get_logger(__name__)

class SequenceInitializer:
    def __init__(self):
        self.logger = get_logger("SequenceInitializer")
        # Map of sequence keys to their corresponding ES index and field
        self.sequence_mappings = {
            "product_id_seq": ("products", "product_id"),
        }

    async def get_max_id_from_elasticsearch(self, index: str, id_field: str) -> int:
        """Get the maximum ID from an Elasticsearch index for a specific field"""
        try:
            query = {
                "aggs": {
                    "max_id": {
                        "max": {
                            "field": id_field
                        }
                    }
                },
                "size": 0  # We don't need the documents, just the aggregation
            }
            
            result = await es.search(
                index=index,
                body=query
            )
            
            max_id = int(result["aggregations"]["max_id"]["value"] or 0)
            self.logger.info(f"Found max {id_field} in {index}: {max_id}")
            return max_id
        except Exception as e:
            self.logger.error(f"Failed to get max ID from {index}", exc_info=True)
            return 0

    async def initialize_sequence(self, sequence_key: str, index: str, id_field: str) -> None:
        """Initialize a single sequence based on database values"""
        try:
            # Get max ID from Elasticsearch
            max_id = await self.get_max_id_from_elasticsearch(index, id_field)
            
            # Initialize sequence with max ID
            sequence = SequenceService(sequence_key)
            current = await sequence.get_current_id()
            
            if current < max_id:
                await sequence.set_current_id(max_id)
                self.logger.info(f"Initialized sequence {sequence_key} to {max_id} from database")
            else:
                self.logger.info(f"Sequence {sequence_key} already at {current}, higher than database max {max_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize sequence {sequence_key}", exc_info=True)
            raise

    async def initialize_all_sequences(self) -> None:
        """Initialize all configured sequences based on database values"""
        self.logger.info("Starting sequence initialization from database")
        
        for sequence_key, (index, id_field) in self.sequence_mappings.items():
            try:
                await self.initialize_sequence(sequence_key, index, id_field)
            except Exception as e:
                self.logger.error(f"Failed to initialize sequence {sequence_key}", exc_info=True)
                raise

        self.logger.info("Completed sequence initialization from database")

# Create a singleton instance
sequence_initializer = SequenceInitializer() 