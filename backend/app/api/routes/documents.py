"""Document management endpoints"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.core.database import get_db
from app.models.document import Document
from app.schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentCreateResponse
)
from app.worker.tasks import index_document, delete_document as delete_document_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


def get_tenant_id(x_tenant_id: str = Header(..., alias="X-Tenant-ID")) -> UUID:
    """Extract and validate tenant ID from header"""
    try:
        return UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Tenant-ID header format"
        )


@router.post("", response_model=DocumentCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_document(
    document: DocumentCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Index a new document (asynchronous processing)

    Returns 202 Accepted immediately, document is indexed in background
    """
    try:
        # Create document in PostgreSQL with pending status
        new_doc = Document(
            tenant_id=tenant_id,
            title=document.title,
            content=document.content,
            metadata=document.metadata or {},
            status="pending"
        )

        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)

        logger.info(f"Created document {new_doc.id} for tenant {tenant_id}")

        # Queue for asynchronous indexing
        index_document.delay(
            document_id=str(new_doc.id),
            tenant_id=str(tenant_id),
            title=new_doc.title,
            content=new_doc.content,
            metadata=new_doc.metadata
        )

        return DocumentCreateResponse(
            id=new_doc.id,
            status="pending",
            message="Document queued for indexing"
        )

    except Exception as e:
        logger.error(f"Failed to create document: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """Retrieve a document by ID"""
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.tenant_id == tenant_id  # Tenant isolation
        ).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )

        return document

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}"
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """Delete a document (asynchronous processing)"""
    try:
        # Check if document exists and belongs to tenant
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.tenant_id == tenant_id
        ).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )

        # Queue for asynchronous deletion
        delete_document_task.delay(
            document_id=str(document_id),
            tenant_id=str(tenant_id)
        )

        logger.info(f"Queued deletion of document {document_id} for tenant {tenant_id}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )
