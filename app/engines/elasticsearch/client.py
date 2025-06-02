import os
from urllib.parse import urlparse
from elasticsearch import AsyncElasticsearch
from app.engines.logging import get_logger

logger = get_logger(__name__)

logger.info("Initializing Elasticsearch client")
es_api_key = os.getenv("ELASTICSEARCH_API_KEY", None)
es_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
parsed = urlparse(es_url)
use_ssl = parsed.scheme == "https"

es_kwargs = {}
if use_ssl:
    es_kwargs["verify_certs"] = os.getenv("ELASTICSEARCH_USE_SSL", "false").lower() == "true"
    ca_certs = os.getenv("ELASTICSEARCH_CA_CERTS", None)
    if ca_certs:
        es_kwargs["ca_certs"] = ca_certs

if es_api_key:
    es = AsyncElasticsearch(
        es_url,
        api_key=es_api_key,
        **es_kwargs
    )
else:
    es = AsyncElasticsearch(
        es_url,
        basic_auth=(
            os.getenv("ELASTICSEARCH_USERNAME", "elastic"),
            os.getenv("ELASTICSEARCH_PASSWORD", "")
        ),
        **es_kwargs
    )
