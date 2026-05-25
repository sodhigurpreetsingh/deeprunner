"""Elasticsearch service for document indexing and search"""
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone
from elasticsearch import Elasticsearch, exceptions as es_exceptions
from app.core.config import settings

logger = logging.getLogger(__name__)


class ElasticsearchService:
    """Service for managing Elasticsearch operations"""

    def __init__(self):
        self.client: Optional[Elasticsearch] = None
        self.index_prefix = settings.ELASTICSEARCH_INDEX_PREFIX

    def connect(self):
        """Initialize Elasticsearch client with connection pooling"""
        try:
            self.client = Elasticsearch(
                [settings.elasticsearch_url],
                max_retries=3,
                retry_on_timeout=True,
                request_timeout=settings.SEARCH_TIMEOUT_SECONDS
            )
            # Test connection with info() instead of ping()
            info = self.client.info()
            logger.info(f"Connected to Elasticsearch at {settings.elasticsearch_url} - version {info['version']['number']}")
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            raise

    def get_index_name(self, tenant_id: UUID) -> str:
        """Get index name for a tenant"""
        return f"{self.index_prefix}_{str(tenant_id).replace('-', '_')}"

    def create_index(self, tenant_id: UUID) -> bool:
        """Create index for a tenant with proper mappings"""
        index_name = self.get_index_name(tenant_id)

        if self.client.indices.exists(index=index_name):
            logger.info(f"Index {index_name} already exists")
            return True

        index_body = {
            "settings": {
                "number_of_shards": 3,
                "number_of_replicas": 2,
                "refresh_interval": "1s",
                "analysis": {
                    "analyzer": {
                        "standard": {
                            "type": "standard"
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "tenant_id": {"type": "keyword"},
                    "title": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "content": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "metadata": {
                        "type": "object",
                        "enabled": False
                    },
                    "indexed_at": {"type": "date"}
                }
            }
        }

        try:
            self.client.indices.create(index=index_name, body=index_body)
            logger.info(f"Created index: {index_name}")
            return True
        except es_exceptions.RequestError as e:
            logger.error(f"Failed to create index {index_name}: {e}")
            return False

    def index_document(
        self,
        tenant_id: UUID,
        document_id: UUID,
        title: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """Index a document in Elasticsearch"""
        index_name = self.get_index_name(tenant_id)

        # Create index if it doesn't exist
        self.create_index(tenant_id)

        doc_body = {
            "id": str(document_id),
            "tenant_id": str(tenant_id),
            "title": title,
            "content": content,
            "metadata": metadata,
            "indexed_at": datetime.now(timezone.utc).isoformat()
        }

        try:
            self.client.index(
                index=index_name,
                id=str(document_id),
                document=doc_body
            )
            logger.info(f"Indexed document {document_id} in {index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to index document {document_id}: {e}")
            return False

    def search_documents(
        self,
        tenant_id: UUID,
        query: str,
        page: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """Search documents with full-text search and relevance ranking"""
        index_name = self.get_index_name(tenant_id)

        # Check if index exists
        if not self.client.indices.exists(index=index_name):
            logger.warning(f"Index {index_name} does not exist")
            return {
                "total": 0,
                "results": [],
                "took_ms": 0
            }

        from_offset = (page - 1) * size

        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^2", "content"],  # Title boosted 2x
                                "type": "best_fields",
                                "operator": "or",
                                "fuzziness": "AUTO"
                            }
                        },
                        {
                            "term": {
                                "tenant_id": str(tenant_id)  # Defense in depth
                            }
                        }
                    ]
                }
            },
            "highlight": {
                "fields": {
                    "title": {},
                    "content": {
                        "fragment_size": 150,
                        "number_of_fragments": 1
                    }
                },
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"]
            },
            "from": from_offset,
            "size": size,
            "_source": ["id", "title", "metadata"]
        }

        try:
            response = self.client.search(index=index_name, body=search_body)

            hits = response['hits']['hits']
            total = response['hits']['total']['value']
            took_ms = response['took']

            results = []
            for hit in hits:
                # Get snippet from highlight or fallback to content
                snippet = ""
                if 'highlight' in hit:
                    if 'content' in hit['highlight']:
                        snippet = hit['highlight']['content'][0]
                    elif 'title' in hit['highlight']:
                        snippet = hit['highlight']['title'][0]

                results.append({
                    "id": hit['_source']['id'],
                    "title": hit['_source']['title'],
                    "snippet": snippet,
                    "score": hit['_score'],
                    "metadata": hit['_source'].get('metadata', {})
                })

            return {
                "total": total,
                "results": results,
                "took_ms": took_ms
            }

        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return {
                "total": 0,
                "results": [],
                "took_ms": 0
            }

    def delete_document(self, tenant_id: UUID, document_id: UUID) -> bool:
        """Delete a document from Elasticsearch"""
        index_name = self.get_index_name(tenant_id)

        try:
            self.client.delete(index=index_name, id=str(document_id))
            logger.info(f"Deleted document {document_id} from {index_name}")
            return True
        except es_exceptions.NotFoundError:
            logger.warning(f"Document {document_id} not found in {index_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False

    def health_check(self) -> str:
        """Check Elasticsearch health"""
        try:
            if self.client:
                cluster_health = self.client.cluster.health()
                status = cluster_health['status']
                return status  # green, yellow, or red
            return "down"
        except Exception as e:
            logger.error(f"Elasticsearch health check failed: {e}")
            return "down"

    def close(self):
        """Close Elasticsearch client"""
        if self.client:
            self.client.close()
            logger.info("Elasticsearch client closed")


# Singleton instance
elasticsearch_service = ElasticsearchService()
