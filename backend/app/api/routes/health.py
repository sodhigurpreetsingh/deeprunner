"""Health check endpoint with dependency monitoring"""
import logging
import time
from fastapi import APIRouter, status
from sqlalchemy import text
from app.schemas.health import HealthResponse, DependencyStatus
from app.services.elasticsearch_service import elasticsearch_service
from app.services.cache_service import cache_service
from app.core.database import sync_engine
from kombu import Connection
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

# Track application start time for uptime calculation
app_start_time = time.time()


def check_postgres() -> str:
    """Check PostgreSQL connectivity"""
    try:
        with sync_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return "up"
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        return "down"


def check_rabbitmq() -> str:
    """Check RabbitMQ connectivity"""
    try:
        with Connection(settings.rabbitmq_url) as conn:
            conn.connect()
        return "up"
    except Exception as e:
        logger.error(f"RabbitMQ health check failed: {e}")
        return "down"


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Comprehensive health check endpoint

    Returns:
    - Overall status (healthy if all dependencies are up)
    - Individual dependency status
    - Application uptime
    """
    # Check all dependencies
    postgres_status = check_postgres()
    elasticsearch_status = elasticsearch_service.health_check()
    redis_status = cache_service.health_check()
    rabbitmq_status = check_rabbitmq()

    # Determine overall status
    all_up = all([
        postgres_status == "up",
        elasticsearch_status in ["green", "yellow"],  # Yellow is acceptable
        redis_status == "up",
        rabbitmq_status == "up"
    ])

    overall_status = "healthy" if all_up else "unhealthy"

    # Calculate uptime
    uptime_seconds = time.time() - app_start_time

    # Map Elasticsearch status to simple up/down
    es_simple_status = "up" if elasticsearch_status in ["green", "yellow"] else "down"

    return HealthResponse(
        status=overall_status,
        dependencies=DependencyStatus(
            postgres=postgres_status,
            elasticsearch=es_simple_status,
            redis=redis_status,
            rabbitmq=rabbitmq_status
        ),
        uptime_seconds=round(uptime_seconds, 2)
    )


@router.get("/health/detailed", include_in_schema=False)
async def detailed_health_check():
    """
    Detailed health check for ops/monitoring

    Includes additional metrics and diagnostics
    """
    postgres_status = check_postgres()
    elasticsearch_status = elasticsearch_service.health_check()
    redis_status = cache_service.health_check()
    rabbitmq_status = check_rabbitmq()

    # Get cache statistics
    cache_stats = cache_service.get_cache_stats()

    return {
        "status": "healthy" if all([
            postgres_status == "up",
            elasticsearch_status in ["green", "yellow"],
            redis_status == "up",
            rabbitmq_status == "up"
        ]) else "unhealthy",
        "dependencies": {
            "postgres": {
                "status": postgres_status,
                "pool_size": sync_engine.pool.size() if postgres_status == "up" else None
            },
            "elasticsearch": {
                "status": elasticsearch_status,
                "url": settings.elasticsearch_url
            },
            "redis": {
                "status": redis_status,
                "stats": cache_stats
            },
            "rabbitmq": {
                "status": rabbitmq_status,
                "url": settings.rabbitmq_url
            }
        },
        "uptime_seconds": round(time.time() - app_start_time, 2)
    }
