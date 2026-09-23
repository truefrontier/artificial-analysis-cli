"""Tests for digest functions."""

import json
from pathlib import Path

import pytest

from aanalysis.digest import (
    filter_models,
    get_coding_index,
    get_intelligence_index,
    get_open_digest,
    is_open_weight,
    normalize_model,
    pick_recommendation,
    rank_by_coding,
    rank_by_intelligence,
    rank_by_smart_cheap,
    rank_by_smart_fast,
)


@pytest.fixture
def models():
    """Load test fixture models."""
    fixture_path = Path(__file__).parent / "fixtures" / "models.json"
    data = json.loads(fixture_path.read_text())
    return [normalize_model(m) for m in data["models"]]


def test_is_open_weight(models):
    """Test open-weight detection."""
    # Llama should be detected as open
    llama = next(m for m in models if "Llama" in m["name"])
    assert is_open_weight(llama) is True
    
    # GPT-4 should be proprietary
    gpt4 = next(m for m in models if "GPT-4" in m["name"])
    assert is_open_weight(gpt4) is False


def test_get_intelligence_index(models):
    """Test intelligence index extraction."""
    claude = next(m for m in models if "Claude" in m["name"])
    intel = get_intelligence_index(claude)
    assert intel == 87.1


def test_get_coding_index(models):
    """Test coding index extraction."""
    deepseek = next(m for m in models if "DeepSeek" in m["name"])
    coding = get_coding_index(deepseek)
    assert coding == 82.1


def test_rank_by_intelligence(models):
    """Test ranking by intelligence."""
    ranked = rank_by_intelligence(models, limit=3)
    assert len(ranked) == 3
    # Claude should be top
    assert "Claude" in ranked[0]["name"]
    # Intelligence should be descending
    intels = [get_intelligence_index(m) for m in ranked]
    assert intels == sorted(intels, reverse=True)


def test_rank_by_coding(models):
    """Test ranking by coding capability."""
    ranked = rank_by_coding(models, limit=3)
    assert len(ranked) >= 1
    # Claude should rank high
    assert any("Claude" in m["name"] or "DeepSeek" in m["name"] for m in ranked[:2])


def test_rank_by_smart_fast(models):
    """Test ranking by smart+fast composite."""
    ranked = rank_by_smart_fast(models, limit=3)
    assert len(ranked) == 3
    # Should have pareto markers
    assert "_pareto_intel_speed" in ranked[0]


def test_rank_by_smart_cheap(models):
    """Test ranking by cost efficiency."""
    ranked = rank_by_smart_cheap(models, limit=3)
    assert len(ranked) >= 1
    # DeepSeek should rank high (cheap and decent)
    names = [m["name"] for m in ranked[:3]]
    assert any("DeepSeek" in name for name in names)


def test_filter_models(models):
    """Test model filtering."""
    # Filter by creator
    meta_models = filter_models(models, creator="Meta")
    assert len(meta_models) == 1
    assert "Llama" in meta_models[0]["name"]
    
    # Filter by min intelligence
    smart_models = filter_models(models, min_intelligence=80.0)
    assert all(get_intelligence_index(m) >= 80.0 for m in smart_models)


def test_get_open_digest(models):
    """Test open-weight digest."""
    digest = get_open_digest(models, limit=3)
    assert "open_models" in digest
    assert "proprietary_comparison" in digest
    assert "intelligence_gap" in digest
    
    # All open models should be marked
    assert all(m["_open_guess"] for m in digest["open_models"])
    
    # Gap should be positive (proprietary ahead)
    assert digest["intelligence_gap"] is not None
    assert digest["intelligence_gap"] > 0


def test_pick_recommendation(models):
    """Test picking recommendations."""
    # Test frontier pick
    frontier = pick_recommendation(models, "frontier")
    assert frontier["recommendation"] is not None
    assert "Claude" in frontier["recommendation"]["name"] or "GPT-4" in frontier["recommendation"]["name"]
    
    # Test local pick (should prefer open models)
    local = pick_recommendation(models, "local")
    assert local["recommendation"] is not None
    assert is_open_weight(local["recommendation"])
    
    # Test coding pick
    coding = pick_recommendation(models, "coding-agent")
    assert coding["recommendation"] is not None
    
    # Test cheap API
    cheap = pick_recommendation(models, "cheap-api")
    assert cheap["recommendation"] is not None
