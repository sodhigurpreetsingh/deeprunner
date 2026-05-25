from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID


class TenantCreate(BaseModel):
    """Schema for creating a new tenant"""
    name: str = Field(..., min_length=1, max_length=255, description="Tenant name")
    rate_limit_per_minute: int = Field(default=100, ge=1, le=10000, description="Rate limit per minute")


class TenantResponse(BaseModel):
    """Schema for tenant response"""
    id: UUID
    name: str
    rate_limit_per_minute: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
