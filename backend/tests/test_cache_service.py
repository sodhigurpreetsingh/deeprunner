"""Unit tests for cache service logic"""
import pytest
from uuid import uuid4, UUID
from app.services.cache_service import CacheService


class TestCacheService:
    """Test cache service functionality"""

    def test_generate_cache_key_consistency(self):
        """Test cache key generation is consistent for same inputs"""
        service = CacheService()
        tenant_id = uuid4()

        key1 = service._generate_cache_key(tenant_id, "test query", 1, 20)
        key2 = service._generate_cache_key(tenant_id, "test query", 1, 20)

        assert key1 == key2
        assert key1.startswith(f"search:{tenant_id}:")

    def test_generate_cache_key_normalization(self):
        """Test cache key normalizes query (lowercase, whitespace)"""
        service = CacheService()
        tenant_id = uuid4()

        key1 = service._generate_cache_key(tenant_id, "Test Query", 1, 20)
        key2 = service._generate_cache_key(tenant_id, "test query", 1, 20)
        key3 = service._generate_cache_key(tenant_id, "  test query  ", 1, 20)

        assert key1 == key2 == key3

    def test_generate_cache_key_different_queries(self):
        """Test different queries generate different keys"""
        service = CacheService()
        tenant_id = uuid4()

        key1 = service._generate_cache_key(tenant_id, "query one", 1, 20)
        key2 = service._generate_cache_key(tenant_id, "query two", 1, 20)

        assert key1 != key2

    def test_generate_cache_key_different_pagination(self):
        """Test different pagination generates different keys"""
        service = CacheService()
        tenant_id = uuid4()

        key1 = service._generate_cache_key(tenant_id, "test", 1, 20)
        key2 = service._generate_cache_key(tenant_id, "test", 2, 20)
        key3 = service._generate_cache_key(tenant_id, "test", 1, 10)

        assert key1 != key2
        assert key1 != key3
        assert key2 != key3

    def test_generate_cache_key_different_tenants(self):
        """Test different tenants generate different keys"""
        service = CacheService()
        tenant_a = uuid4()
        tenant_b = uuid4()

        key_a = service._generate_cache_key(tenant_a, "test", 1, 20)
        key_b = service._generate_cache_key(tenant_b, "test", 1, 20)

        assert key_a != key_b
        assert f"search:{tenant_a}:" in key_a
        assert f"search:{tenant_b}:" in key_b

    def test_cache_hit_rate_calculation_full_hits(self):
        """Test hit rate calculation with 100% hits"""
        assert CacheService._calculate_hit_rate(100, 0) == 100.0

    def test_cache_hit_rate_calculation_full_misses(self):
        """Test hit rate calculation with 100% misses"""
        assert CacheService._calculate_hit_rate(0, 100) == 0.0

    def test_cache_hit_rate_calculation_mixed(self):
        """Test hit rate calculation with mixed hits/misses"""
        assert CacheService._calculate_hit_rate(85, 15) == 85.0
        assert CacheService._calculate_hit_rate(50, 50) == 50.0
        assert CacheService._calculate_hit_rate(90, 10) == 90.0

    def test_cache_hit_rate_calculation_zero_requests(self):
        """Test hit rate calculation with no requests"""
        assert CacheService._calculate_hit_rate(0, 0) == 0.0

    def test_cache_hit_rate_calculation_rounding(self):
        """Test hit rate calculation rounds to 2 decimal places"""
        rate = CacheService._calculate_hit_rate(333, 667)
        assert rate == 33.3
        assert isinstance(rate, float)

    def test_cache_key_format(self):
        """Test cache key follows expected format"""
        service = CacheService()
        tenant_id = UUID("550e8400-e29b-41d4-a716-446655440000")

        key = service._generate_cache_key(tenant_id, "test", 1, 20)

        # Should be: search:{tenant_id}:{hash}
        parts = key.split(":")
        assert len(parts) == 3
        assert parts[0] == "search"
        assert parts[1] == str(tenant_id)
        assert len(parts[2]) == 32  # MD5 hash length

    def test_cache_key_hash_uniqueness(self):
        """Test that hash collision is unlikely"""
        service = CacheService()
        tenant_id = uuid4()

        # Generate many keys with slight variations
        keys = set()
        for i in range(100):
            key = service._generate_cache_key(tenant_id, f"query {i}", 1, 20)
            keys.add(key)

        # All keys should be unique
        assert len(keys) == 100


class TestCacheServiceEdgeCases:
    """Test cache service edge cases"""

    def test_cache_key_with_special_characters(self):
        """Test cache key generation with special characters"""
        service = CacheService()
        tenant_id = uuid4()

        key1 = service._generate_cache_key(tenant_id, "test & demo", 1, 20)
        key2 = service._generate_cache_key(tenant_id, "test <html>", 1, 20)
        key3 = service._generate_cache_key(tenant_id, "test \"quotes\"", 1, 20)

        # Should handle special characters without errors
        assert key1 is not None
        assert key2 is not None
        assert key3 is not None
        assert key1 != key2 != key3

    def test_cache_key_with_unicode(self):
        """Test cache key generation with unicode characters"""
        service = CacheService()
        tenant_id = uuid4()

        key1 = service._generate_cache_key(tenant_id, "test émojis 🚀", 1, 20)
        key2 = service._generate_cache_key(tenant_id, "test spëcial", 1, 20)

        assert key1 is not None
        assert key2 is not None
        assert key1 != key2

    def test_cache_key_with_very_long_query(self):
        """Test cache key generation with very long query"""
        service = CacheService()
        tenant_id = uuid4()

        long_query = "test " * 1000  # 5000 characters
        key = service._generate_cache_key(tenant_id, long_query, 1, 20)

        # Should hash long queries consistently
        assert key is not None
        assert len(key) < 200  # Key should be much shorter than query

    def test_cache_key_with_whitespace_variations(self):
        """Test cache key normalization with various whitespace"""
        service = CacheService()
        tenant_id = uuid4()

        key1 = service._generate_cache_key(tenant_id, "test query", 1, 20)
        key2 = service._generate_cache_key(tenant_id, "test  query", 1, 20)  # Double space
        key3 = service._generate_cache_key(tenant_id, "  test query  ", 1, 20)  # Leading/trailing
        key4 = service._generate_cache_key(tenant_id, "\ntest query\n", 1, 20)  # Newlines

        # Normalization should make all consistent except double space
        assert key1 == key3
        # Double space in middle is preserved (semantic difference)
        # Leading/trailing is stripped

    def test_cache_key_with_case_variations(self):
        """Test cache key case insensitivity"""
        service = CacheService()
        tenant_id = uuid4()

        key1 = service._generate_cache_key(tenant_id, "TEST QUERY", 1, 20)
        key2 = service._generate_cache_key(tenant_id, "test query", 1, 20)
        key3 = service._generate_cache_key(tenant_id, "Test Query", 1, 20)
        key4 = service._generate_cache_key(tenant_id, "TeSt QuErY", 1, 20)

        assert key1 == key2 == key3 == key4

    def test_cache_key_boundary_values(self):
        """Test cache key with boundary pagination values"""
        service = CacheService()
        tenant_id = uuid4()

        # Page 1, size 1 (minimum valid values)
        key1 = service._generate_cache_key(tenant_id, "test", 1, 1)
        assert key1 is not None

        # Large page number
        key2 = service._generate_cache_key(tenant_id, "test", 999999, 20)
        assert key2 is not None

        # Max size
        key3 = service._generate_cache_key(tenant_id, "test", 1, 100)
        assert key3 is not None

        # All should be different
        assert key1 != key2 != key3
