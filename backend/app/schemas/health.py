from pydantic import BaseModel
from typing import Dict


class DependencyStatus(BaseModel):
    """Schema for dependency health status"""
    postgres: str
    elasticsearch: str
    redis: str
    rabbitmq: str


class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    dependencies: DependencyStatus
    uptime_seconds: float
