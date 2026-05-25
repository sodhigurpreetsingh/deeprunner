"""Pytest configuration and fixtures"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def sample_document_data():
    """Sample document data for testing"""
    return {
        "title": "Test Document",
        "content": "This is test content for the document search service.",
        "metadata": {
            "author": "Test User",
            "category": "Testing",
            "tags": ["test", "sample"]
        }
    }


@pytest.fixture
def sample_tenant_id():
    """Sample tenant ID for testing"""
    from uuid import UUID
    return UUID("550e8400-e29b-41d4-a716-446655440000")


@pytest.fixture
def sample_search_query():
    """Sample search query for testing"""
    return {
        "q": "test query",
        "page": 1,
        "size": 20
    }
