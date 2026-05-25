"""Search endpoints"""
import logging
import time
from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from uuid import UUID
from typing import Optional

from app.schemas.document import SearchResponse, SearchResult
from app.services.elasticsearch_service import elasticsearch_service
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


def get_tenant_id(x_tenant_id: str = Header(..., alias="X-Tenant-ID")) -> UUID:
    """Extract and validate tenant ID from header"""
    try:
        return UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Tenant-ID header format"
        )


@router.get("", response_model=SearchResponse)
async def search_documents(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Results per page"),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """
    Search documents with full-text search and caching

    Performance targets:
    - Cache hit: <10ms
    - Cache miss: <500ms (p95)
    """
    start_time = time.time()

    try:
        # Check cache first
        cached_result = cache_service.get_search_result(
            tenant_id=tenant_id,
            query=q,
            page=page,
            size=size
        )

        if cached_result:
            # Add timing info
            took_ms = (time.time() - start_time) * 1000
            cached_result['took_ms'] = round(took_ms, 2)
            logger.info(f"Cache HIT for query '{q}' (tenant: {tenant_id}) - {took_ms:.2f}ms")
            return SearchResponse(**cached_result)

        # Cache miss - search Elasticsearch
        search_result = elasticsearch_service.search_documents(
            tenant_id=tenant_id,
            query=q,
            page=page,
            size=size
        )

        # Convert to response format
        results = [
            SearchResult(
                id=result['id'],
                title=result['title'],
                snippet=result['snippet'],
                score=result['score'],
                metadata=result['metadata']
            )
            for result in search_result['results']
        ]

        response = SearchResponse(
            total=search_result['total'],
            results=results,
            page=page,
            size=size,
            took_ms=search_result['took_ms']
        )

        # Cache the result
        cache_service.set_search_result(
            tenant_id=tenant_id,
            query=q,
            page=page,
            size=size,
            result=response.model_dump()
        )

        total_time_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Search completed for query '{q}' (tenant: {tenant_id}) - "
            f"{total_time_ms:.2f}ms total, {search_result['took_ms']}ms ES, "
            f"{search_result['total']} results"
        )

        return response

    except Exception as e:
        logger.error(f"Search failed for query '{q}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )
