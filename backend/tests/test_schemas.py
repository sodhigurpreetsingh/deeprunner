"""Unit tests for Pydantic schemas"""
import pytest
from pydantic import ValidationError
from uuid import uuid4
from app.schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentCreateResponse,
    SearchRequest,
    SearchResult,
    SearchResponse
)
from app.schemas.tenant import TenantCreate, TenantResponse
from app.schemas.health import HealthResponse, DependencyStatus
from datetime import datetime


class TestDocumentSchemas:
    """Test document-related schemas"""

    def test_document_create_valid(self):
        """Test valid document creation"""
        doc = DocumentCreate(
            title="Test Document",
            content="This is test content",
            metadata={"author": "Test User", "category": "Testing"}
        )
        assert doc.title == "Test Document"
        assert doc.content == "This is test content"
        assert doc.metadata["author"] == "Test User"

    def test_document_create_empty_title(self):
        """Test document with empty title fails"""
        with pytest.raises(ValidationError) as exc_info:
            DocumentCreate(title="", content="Content")
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_document_create_empty_content(self):
        """Test document with empty content fails"""
        with pytest.raises(ValidationError) as exc_info:
            DocumentCreate(title="Title", content="")
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_document_create_missing_title(self):
        """Test document without title fails"""
        with pytest.raises(ValidationError) as exc_info:
            DocumentCreate(content="Content")
        assert "Field required" in str(exc_info.value)

    def test_document_create_missing_content(self):
        """Test document without content fails"""
        with pytest.raises(ValidationError) as exc_info:
            DocumentCreate(title="Title")
        assert "Field required" in str(exc_info.value)

    def test_document_create_title_too_long(self):
        """Test document with title > 500 characters"""
        with pytest.raises(ValidationError) as exc_info:
            DocumentCreate(title="A" * 501, content="Content")
        assert "String should have at most 500 characters" in str(exc_info.value)

    def test_document_create_default_metadata(self):
        """Test default empty metadata"""
        doc = DocumentCreate(title="Test", content="Content")
        assert doc.metadata == {}

    def test_document_create_with_special_characters(self):
        """Test document with special characters"""
        doc = DocumentCreate(
            title="Test émojis 🚀",
            content="Special chars: <>&\"'",
            metadata={"key": "value with spëcial"}
        )
        assert "🚀" in doc.title
        assert "<>&" in doc.content

    def test_search_request_valid(self):
        """Test valid search request"""
        req = SearchRequest(q="test query", page=1, size=20)
        assert req.q == "test query"
        assert req.page == 1
        assert req.size == 20

    def test_search_request_default_pagination(self):
        """Test search request with default pagination"""
        req = SearchRequest(q="test")
        assert req.page == 1
        assert req.size == 20

    def test_search_request_empty_query(self):
        """Test search with empty query fails"""
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(q="", page=1, size=20)
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_search_request_page_zero(self):
        """Test search with page=0 fails"""
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(q="test", page=0, size=20)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_search_request_negative_page(self):
        """Test search with negative page fails"""
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(q="test", page=-1, size=20)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_search_request_size_zero(self):
        """Test search with size=0 fails"""
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(q="test", page=1, size=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_search_request_size_too_large(self):
        """Test search with size > 100 fails"""
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(q="test", page=1, size=101)
        assert "less than or equal to 100" in str(exc_info.value)

    def test_search_request_max_size(self):
        """Test search with max size=100 succeeds"""
        req = SearchRequest(q="test", page=1, size=100)
        assert req.size == 100

    def test_search_result_valid(self):
        """Test valid search result"""
        result = SearchResult(
            id="550e8400-e29b-41d4-a716-446655440000",
            title="Test Document",
            snippet="This is a <mark>test</mark> snippet",
            score=12.45,
            metadata={"author": "Test"}
        )
        assert result.id == "550e8400-e29b-41d4-a716-446655440000"
        assert "<mark>test</mark>" in result.snippet
        assert result.score == 12.45

    def test_search_response_valid(self):
        """Test valid search response"""
        results = [
            SearchResult(
                id=str(uuid4()),
                title=f"Doc {i}",
                snippet=f"Snippet {i}",
                score=10.0 - i,
                metadata={}
            )
            for i in range(5)
        ]

        response = SearchResponse(
            total=100,
            results=results,
            page=1,
            size=20,
            took_ms=87.5
        )

        assert response.total == 100
        assert len(response.results) == 5
        assert response.page == 1
        assert response.took_ms == 87.5

    def test_search_response_empty_results(self):
        """Test search response with no results"""
        response = SearchResponse(
            total=0,
            results=[],
            page=1,
            size=20,
            took_ms=5.2
        )
        assert response.total == 0
        assert len(response.results) == 0


class TestTenantSchemas:
    """Test tenant-related schemas"""

    def test_tenant_create_valid(self):
        """Test valid tenant creation"""
        tenant = TenantCreate(
            name="Test Tenant",
            rate_limit_per_minute=200
        )
        assert tenant.name == "Test Tenant"
        assert tenant.rate_limit_per_minute == 200

    def test_tenant_create_default_rate_limit(self):
        """Test default rate limit"""
        tenant = TenantCreate(name="Test")
        assert tenant.rate_limit_per_minute == 100

    def test_tenant_create_empty_name(self):
        """Test tenant with empty name fails"""
        with pytest.raises(ValidationError) as exc_info:
            TenantCreate(name="")
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_tenant_create_name_too_long(self):
        """Test tenant with name > 255 characters"""
        with pytest.raises(ValidationError) as exc_info:
            TenantCreate(name="A" * 256)
        assert "String should have at most 255 characters" in str(exc_info.value)

    def test_tenant_create_rate_limit_too_low(self):
        """Test tenant with rate_limit < 1"""
        with pytest.raises(ValidationError) as exc_info:
            TenantCreate(name="Test", rate_limit_per_minute=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_tenant_create_rate_limit_too_high(self):
        """Test tenant with rate_limit > 10000"""
        with pytest.raises(ValidationError) as exc_info:
            TenantCreate(name="Test", rate_limit_per_minute=10001)
        assert "less than or equal to 10000" in str(exc_info.value)


class TestHealthSchemas:
    """Test health check schemas"""

    def test_dependency_status_valid(self):
        """Test valid dependency status"""
        status = DependencyStatus(
            postgres="up",
            elasticsearch="up",
            redis="up",
            rabbitmq="up"
        )
        assert status.postgres == "up"
        assert status.elasticsearch == "up"

    def test_health_response_healthy(self):
        """Test healthy system response"""
        response = HealthResponse(
            status="healthy",
            dependencies=DependencyStatus(
                postgres="up",
                elasticsearch="up",
                redis="up",
                rabbitmq="up"
            ),
            uptime_seconds=123.45
        )
        assert response.status == "healthy"
        assert response.uptime_seconds == 123.45

    def test_health_response_unhealthy(self):
        """Test unhealthy system response"""
        response = HealthResponse(
            status="unhealthy",
            dependencies=DependencyStatus(
                postgres="up",
                elasticsearch="down",
                redis="up",
                rabbitmq="up"
            ),
            uptime_seconds=500.0
        )
        assert response.status == "unhealthy"
        assert response.dependencies.elasticsearch == "down"
