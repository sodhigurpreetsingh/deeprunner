"""Celery tasks for document processing"""
import logging
from uuid import UUID
from typing import Dict, Any, List
from celery import Task
from elasticsearch import exceptions as es_exceptions
from app.worker.celery_app import celery_app
from app.services.elasticsearch_service import elasticsearch_service
from app.services.cache_service import cache_service
from app.core.database import get_sync_db
from app.models.document import Document
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """Base task with callbacks for setup/teardown"""

    def __call__(self, *args, **kwargs):
        # Ensure connections are initialized
        if not elasticsearch_service.client:
            elasticsearch_service.connect()
        if not cache_service.client:
            cache_service.connect()
        return super().__call__(*args, **kwargs)


@celery_app.task(
    bind=True,
    base=CallbackTask,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,)
)
def index_document(
    self,
    document_id: str,
    tenant_id: str,
    title: str,
    content: str,
    metadata: Dict[str, Any]
):
    """Index a single document in Elasticsearch"""
    logger.info(f"Indexing document {document_id} for tenant {tenant_id}")

    try:
        doc_uuid = UUID(document_id)
        tenant_uuid = UUID(tenant_id)

        # Index in Elasticsearch
        success = elasticsearch_service.index_document(
            tenant_id=tenant_uuid,
            document_id=doc_uuid,
            title=title,
            content=content,
            metadata=metadata
        )

        if success:
            # Update document status in PostgreSQL
            db: Session = next(get_sync_db())
            try:
                doc = db.query(Document).filter(Document.id == doc_uuid).first()
                if doc:
                    doc.status = "indexed"
                    db.commit()
                    logger.info(f"Document {document_id} successfully indexed")

                # Invalidate cache for this tenant
                cache_service.invalidate_tenant_cache(tenant_uuid)

            finally:
                db.close()

            return {"status": "success", "document_id": document_id}
        else:
            raise Exception("Failed to index document in Elasticsearch")

    except Exception as e:
        logger.error(f"Failed to index document {document_id}: {e}")

        # Update document status to failed
        db: Session = next(get_sync_db())
        try:
            doc = db.query(Document).filter(Document.id == UUID(document_id)).first()
            if doc:
                doc.status = "failed"
                doc.error_message = str(e)
                db.commit()
        finally:
            db.close()

        # Retry if retries remaining
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        return {"status": "failed", "document_id": document_id, "error": str(e)}


@celery_app.task(
    bind=True,
    base=CallbackTask,
    max_retries=3,
    default_retry_delay=120
)
def batch_index_documents(self, document_ids: List[str], tenant_id: str):
    """Batch index multiple documents"""
    logger.info(f"Batch indexing {len(document_ids)} documents for tenant {tenant_id}")

    results = []
    for doc_id in document_ids:
        try:
            # Fetch document from database
            db: Session = next(get_sync_db())
            try:
                doc = db.query(Document).filter(Document.id == UUID(doc_id)).first()
                if doc:
                    # Index document
                    success = elasticsearch_service.index_document(
                        tenant_id=UUID(tenant_id),
                        document_id=doc.id,
                        title=doc.title,
                        content=doc.content,
                        metadata=doc.metadata or {}
                    )

                    if success:
                        doc.status = "indexed"
                        results.append({"id": doc_id, "status": "success"})
                    else:
                        doc.status = "failed"
                        doc.error_message = "Elasticsearch indexing failed"
                        results.append({"id": doc_id, "status": "failed"})

                    db.commit()
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Failed to index document {doc_id} in batch: {e}")
            results.append({"id": doc_id, "status": "failed", "error": str(e)})

    # Invalidate cache for tenant
    cache_service.invalidate_tenant_cache(UUID(tenant_id))

    logger.info(f"Batch indexing complete: {len(results)} documents processed")
    return {"total": len(document_ids), "results": results}


@celery_app.task(
    bind=True,
    base=CallbackTask,
    max_retries=2,
    default_retry_delay=30
)
def delete_document(self, document_id: str, tenant_id: str):
    """Delete a document from Elasticsearch and PostgreSQL"""
    logger.info(f"Deleting document {document_id} for tenant {tenant_id}")

    try:
        doc_uuid = UUID(document_id)
        tenant_uuid = UUID(tenant_id)

        # Delete from Elasticsearch
        elasticsearch_service.delete_document(
            tenant_id=tenant_uuid,
            document_id=doc_uuid
        )

        # Delete from PostgreSQL
        db: Session = next(get_sync_db())
        try:
            doc = db.query(Document).filter(Document.id == doc_uuid).first()
            if doc:
                db.delete(doc)
                db.commit()
                logger.info(f"Document {document_id} successfully deleted")
        finally:
            db.close()

        # Invalidate cache
        cache_service.invalidate_document_cache(tenant_uuid, doc_uuid)

        return {"status": "success", "document_id": document_id}

    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        return {"status": "failed", "document_id": document_id, "error": str(e)}
