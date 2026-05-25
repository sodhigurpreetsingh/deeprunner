from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from app.core.database import Base


class Document(Base):
    """Document model with multi-tenant support"""
    __tablename__ = "documents"
    __table_args__ = (
        Index('idx_documents_tenant', 'tenant_id', 'created_at'),
        Index('idx_documents_status', 'status'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    doc_metadata = Column('metadata', JSONB, default={})
    status = Column(String(20), default='pending')  # pending, indexed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Document {self.id} - {self.title[:50]}>"
