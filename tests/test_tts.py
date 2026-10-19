"""Tests for TTS client and digest functions."""

import json
from pathlib import Path

import pytest
from pytest_httpx import HTTPXMock

from aanalysis.client import ArtificialAnalysisClient
from aanalysis.tts_digest import (
    normalize_tts_model,
    filter_tts_models,
    rank_by_elo,
    rank_by_smart_fast_tts,
    rank_by_smart_cheap_tts,
    get_elo,
    get_ci95,
)


@pytest.fixture
def tts_fixture_models():
    """Load test fixture TTS models."""
    fixture_path = Path(__file__).parent / "fixtures" / "tts_models.json"
    return json.loads(fixture_path.read_text())


@pytest.fixture
def tts_models(tts_fixture_models):
    """Load and normalize TTS models."""
    return [normalize_tts_model(m) for m in tts_fixture_models["data"]]


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create client with temp cache dir."""
    cache_dir = tmp_path / "cache"
    monkeypatch.setenv("ARTIFICIAL_ANALYSIS_API_KEY", "test-key")
    return ArtificialAnalysisClient(cache_dir=cache_dir)


def test_list_tts_models(client, tts_fixture_models, httpx_mock: HTTPXMock):
    """Test listing TTS models."""
    httpx_mock.add_response(
        url="https://artificialanalysis.ai/api/v2/data/media/text-to-speech",
        json=tts_fixture_models
    )
    
    response = client.list_tts_models(refresh=True)
    assert response["status"] == "success"
    assert "data" in response
    assert len(response["data"]) == 5


def test_fetch_all_tts_models(client, tts_fixture_models, httpx_mock: HTTPXMock):
    """Test fetching all TTS models."""
    httpx_mock.add_response(
        url="https://artificialanalysis.ai/api/v2/data/media/text-to-speech",
        json=tts_fixture_models
    )
    
    models = client.fetch_all_tts_models(refresh=True)
    assert len(models) == 5
    assert models[0]["name"] == "ElevenLabs v4"


def test_normalize_tts_model(tts_models):
    """Test TTS model normalization."""
    model = tts_models[0]
    assert "model_creator_name" in model
    assert model["model_creator_name"] == "ElevenLabs"


def test_get_elo(tts_models):
    """Test Elo extraction."""
    eleven = next(m for m in tts_models if "ElevenLabs" in m["name"])
    elo = get_elo(eleven)
    assert elo == 1315.2


def test_get_ci95(tts_models):
    """Test CI95 extraction."""
    eleven = next(m for m in tts_models if "ElevenLabs" in m["name"])
    ci = get_ci95(eleven)
    assert ci == 12.5


def test_rank_by_elo(tts_models):
    """Test ranking by Elo."""
    ranked = rank_by_elo(tts_models, limit=3)
    assert len(ranked) == 3
    # ElevenLabs should be top
    assert "ElevenLabs" in ranked[0]["name"]
    # Elo should be descending
    elos = [get_elo(m) for m in ranked]
    assert elos == sorted(elos, reverse=True)


def test_filter_tts_models(tts_models):
    """Test TTS model filtering."""
    # Filter by creator
    google_models = filter_tts_models(tts_models, creator="Google")
    assert len(google_models) == 1
    assert "Gemini" in google_models[0]["name"]
    
    # Filter by min Elo
    high_elo = filter_tts_models(tts_models, min_elo=1280.0)
    assert all(get_elo(m) >= 1280.0 for m in high_elo)


def test_rank_by_smart_fast_tts_no_speed(tts_models):
    """Test smart-fast ranking degrades gracefully without speed data."""
    # Our fixtures don't have speed data
    ranked = rank_by_smart_fast_tts(tts_models, limit=3)
    # Should return empty or fall back to Elo ranking
    assert isinstance(ranked, list)


def test_rank_by_smart_cheap_tts_no_price(tts_models):
    """Test smart-cheap ranking degrades gracefully without price data."""
    # Our fixtures don't have price data
    ranked = rank_by_smart_cheap_tts(tts_models, limit=3)
    # Should return empty list when no price data
    assert ranked == []
