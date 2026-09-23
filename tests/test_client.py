"""Tests for aanalysis client."""

import json
from pathlib import Path

import pytest
from pytest_httpx import HTTPXMock

from aanalysis.client import ArtificialAnalysisClient, AuthError, APIError


@pytest.fixture
def fixture_models():
    """Load test fixture models."""
    fixture_path = Path(__file__).parent / "fixtures" / "models.json"
    return json.loads(fixture_path.read_text())


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create client with temp cache dir."""
    cache_dir = tmp_path / "cache"
    monkeypatch.setenv("ARTIFICIAL_ANALYSIS_API_KEY", "test-key")
    return ArtificialAnalysisClient(cache_dir=cache_dir)


def test_api_key_discovery(tmp_path, monkeypatch):
    """Test API key discovery from environment."""
    monkeypatch.setenv("ARTIFICIAL_ANALYSIS_API_KEY", "env-key")
    client = ArtificialAnalysisClient()
    assert client.api_key == "env-key"


def test_list_models(client, fixture_models, httpx_mock: HTTPXMock):
    """Test listing models."""
    httpx_mock.add_response(
        url="https://artificialanalysis.ai/api/v2/language/models/free?page=1",
        json=fixture_models
    )
    
    response = client.list_models(page=1, refresh=True)
    assert "data" in response
    assert len(response["data"]) == 5


def test_fetch_all_models(client, fixture_models, httpx_mock: HTTPXMock):
    """Test fetching all models across pages."""
    httpx_mock.add_response(
        url="https://artificialanalysis.ai/api/v2/language/models/free?page=1",
        json=fixture_models
    )
    
    models = client.fetch_all_models(refresh=True)
    assert len(models) == 5
    assert models[0]["name"] == "GPT-4o"


def test_auth_error(client, httpx_mock: HTTPXMock):
    """Test authentication error handling."""
    httpx_mock.add_response(
        url="https://artificialanalysis.ai/api/v2/language/models/free?page=1",
        status_code=401,
        json={"error": "Invalid API key"}
    )
    
    with pytest.raises(AuthError):
        client.list_models(page=1, refresh=True)


def test_caching(client, fixture_models, httpx_mock: HTTPXMock, tmp_path):
    """Test response caching."""
    # Mock will be called twice (initial + refresh)
    for _ in range(2):
        httpx_mock.add_response(
            url="https://artificialanalysis.ai/api/v2/language/models/free?page=1",
            json=fixture_models
        )
    
    # First request - hits API
    response1 = client.list_models(page=1)
    assert len(httpx_mock.get_requests()) == 1
    
    # Second request - hits cache
    response2 = client.list_models(page=1)
    assert len(httpx_mock.get_requests()) == 1
    assert response1 == response2
    
    # Third request with refresh - hits API again
    response3 = client.list_models(page=1, refresh=True)
    assert len(httpx_mock.get_requests()) == 2


def test_top_level_pagination(client, httpx_mock: HTTPXMock):
    """Test pagination with top-level pagination object (production bug fix)."""
    # Page 1 with top-level pagination
    page1 = {
        "tier": "free",
        "intelligence_index_version": 4.3,
        "pagination": {
            "page": 1,
            "page_size": 200,
            "total_pages": 2,
            "has_more": True
        },
        "data": [
            {"id": "1", "name": "Model 1", "slug": "model-1"}
        ]
    }
    
    # Page 2 with top-level pagination
    page2 = {
        "tier": "free",
        "intelligence_index_version": 4.3,
        "pagination": {
            "page": 2,
            "page_size": 200,
            "total_pages": 2,
            "has_more": False
        },
        "data": [
            {"id": "2", "name": "Model 2", "slug": "model-2"}
        ]
    }
    
    httpx_mock.add_response(
        url="https://artificialanalysis.ai/api/v2/language/models/free?page=1",
        json=page1
    )
    httpx_mock.add_response(
        url="https://artificialanalysis.ai/api/v2/language/models/free?page=2",
        json=page2
    )
    
    # Fetch all models - should get both pages
    models = client.fetch_all_models(refresh=True)
    assert len(models) == 2
    assert models[0]["name"] == "Model 1"
    assert models[1]["name"] == "Model 2"
    assert len(httpx_mock.get_requests()) == 2
