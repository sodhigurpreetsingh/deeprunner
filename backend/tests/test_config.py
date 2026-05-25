"""Unit tests for configuration"""
import pytest
from app.core.config import settings


class TestConfiguration:
    """Test configuration and settings"""

    def test_app_name(self):
        """Test application name is correct"""
        assert settings.APP_NAME == "Document Search Service"

    def test_postgres_url_generation(self):
        """Test PostgreSQL URL is properly generated"""
        url = settings.postgres_url
        assert "postgresql://" in url
        assert "docsearch" in url
        assert f"{settings.POSTGRES_PORT}" in url

    def test_postgres_async_url_generation(self):
        """Test PostgreSQL async URL is properly generated"""
        url = settings.postgres_async_url
        assert "postgresql+asyncpg://" in url
        assert "docsearch" in url

    def test_elasticsearch_url_generation(self):
        """Test Elasticsearch URL is properly generated"""
        url = settings.elasticsearch_url
        expected = f"{settings.ELASTICSEARCH_SCHEME}://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"
        assert url == expected

    def test_redis_url_generation_without_password(self):
        """Test Redis URL generation without password"""
        # When password is None/empty, URL should not contain auth part
        url = settings.redis_url
        assert "redis://" in url
        assert f"{settings.REDIS_HOST}" in url
        assert f"{settings.REDIS_PORT}" in url
        # Without password, no @ symbol in URL
        if not settings.REDIS_PASSWORD:
            assert "@" not in url

    def test_rabbitmq_url_generation(self):
        """Test RabbitMQ URL is properly generated"""
        url = settings.rabbitmq_url
        assert "amqp://" in url
        assert settings.RABBITMQ_USER in url
        assert f"{settings.RABBITMQ_HOST}" in url
        assert f"{settings.RABBITMQ_PORT}" in url

    def test_cache_ttl_seconds(self):
        """Test cache TTL is configured"""
        assert settings.CACHE_TTL_SECONDS > 0
        assert settings.CACHE_TTL_SECONDS == 300  # 5 minutes

    def test_rate_limit_enabled(self):
        """Test rate limiting is enabled"""
        assert settings.RATE_LIMIT_ENABLED is True

    def test_default_rate_limit(self):
        """Test default rate limit is set"""
        assert settings.DEFAULT_RATE_LIMIT == "100/minute"

    def test_search_timeout(self):
        """Test search timeout is configured"""
        assert settings.SEARCH_TIMEOUT_SECONDS > 0
        assert settings.SEARCH_TIMEOUT_SECONDS <= 10

    def test_max_search_results(self):
        """Test max search results limit"""
        assert settings.MAX_SEARCH_RESULTS > 0
        assert settings.MAX_SEARCH_RESULTS >= 100
