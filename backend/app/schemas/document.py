from pydantic import BaseModel, Field, ConfigDict, field_serializer
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


class DocumentCreate(BaseModel):
    """Schema for creating a new document"""
    title: str = Field(..., min_length=1, max_length=500, description="Document title")
    content: str = Field(..., min_length=1, description="Document content")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")


class DocumentResponse(BaseModel):
    """Schema for document response"""
    id: UUID
    tenant_id: UUID
    title: str
    content: str
    metadata: Dict[str, Any] = Field(validation_alias='doc_metadata', serialization_alias='metadata')
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DocumentCreateResponse(BaseModel):
    """Schema for document creation response"""
    id: UUID
    status: str
    message: str


class SearchResult(BaseModel):
    """Schema for a single search result"""
    id: str
    title: str
    snippet: str
    score: float
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    """Schema for search results response"""
    total: int
    results: List[SearchResult]
    page: int
    size: int
    took_ms: float


class SearchRequest(BaseModel):
    """Schema for search request"""
    q: str = Field(..., min_length=1, description="Search query")
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Results per page")
