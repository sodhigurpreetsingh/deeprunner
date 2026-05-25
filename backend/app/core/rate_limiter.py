"""Tenant-based rate limiting"""
import logging
from typing import Optional
from uuid import UUID
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_tenant_identifier(request: Request) -> str:
    """
    Get tenant identifier for rate limiting

    Uses X-Tenant-ID header if present, otherwise falls back to IP address
    """
    tenant_id = request.headers.get("X-Tenant-ID")

    if tenant_id:
        try:
            # Validate UUID format
            UUID(tenant_id)
            return f"tenant:{tenant_id}"
        except ValueError:
            logger.warning(f"Invalid tenant ID format: {tenant_id}")

    # Fallback to IP-based rate limiting
    return f"ip:{get_remote_address(request)}"


# Initialize rate limiter with tenant-based key function
limiter = Limiter(
    key_func=get_tenant_identifier,
    default_limits=[settings.DEFAULT_RATE_LIMIT] if settings.RATE_LIMIT_ENABLED else []
)


def get_tenant_rate_limit(tenant_id: UUID) -> str:
    """
    Get rate limit for a specific tenant from database

    In production, this would query the tenants table.
    For prototype, using default rate limit.
    """
    # TODO: Query database for tenant-specific rate limit
    # db_tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    # if db_tenant:
    #     return f"{db_tenant.rate_limit_per_minute}/minute"

    return settings.DEFAULT_RATE_LIMIT
