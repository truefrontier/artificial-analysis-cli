#!/usr/bin/env python3
"""Smoke test for aanalysis CLI using test fixtures."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from aanalysis.client import ArtificialAnalysisClient
from aanalysis.digest import (
    normalize_model,
    rank_by_intelligence,
    rank_by_smart_fast,
    rank_by_coding,
    pick_recommendation,
    get_open_digest,
)


def load_fixture_models():
    """Load test fixture models."""
    fixture_path = Path(__file__).parent / "tests" / "fixtures" / "models.json"
    data = json.loads(fixture_path.read_text())
    return [normalize_model(m) for m in data["models"]]


def test_all_json():
    """Test digest all --json with fixtures."""
    print("Testing digest all --json...")
    
    models = load_fixture_models()
    
    # Test each digest
    smartest = rank_by_intelligence(models, limit=5)
    assert len(smartest) > 0
    print(f"  ✓ Smartest: {len(smartest)} models")
    
    smart_fast = rank_by_smart_fast(models, limit=5)
    assert len(smart_fast) > 0
    print(f"  ✓ Smart-fast: {len(smart_fast)} models")
    
    coding = rank_by_coding(models, limit=5)
    assert len(coding) > 0
    print(f"  ✓ Coding: {len(coding)} models")
    
    open_digest = get_open_digest(models, limit=5)
    assert len(open_digest["open_models"]) > 0
    print(f"  ✓ Open: {len(open_digest['open_models'])} models")
    
    # Test picks
    for category in ["local", "cheap-api", "frontier", "coding-agent"]:
        rec = pick_recommendation(models, category)
        assert rec["recommendation"] is not None
        print(f"  ✓ Pick {category}: {rec['recommendation']['name']}")
    
    print("\nAll digest functions work! ✓")


def test_json_output():
    """Test JSON output format."""
    print("\nTesting JSON output format...")
    
    models = load_fixture_models()
    smartest = rank_by_intelligence(models, limit=3)
    
    # Build table data like the CLI does
    from aanalysis.output import build_model_table_data
    table_data = build_model_table_data(smartest)
    
    # Verify structure
    assert len(table_data) == 3
    assert "rank" in table_data[0]
    assert "name" in table_data[0]
    assert "intelligence_index" in table_data[0]
    
    print(f"  ✓ JSON structure valid")
    print(f"\nSample output:")
    print(json.dumps(table_data[:2], indent=2))


if __name__ == "__main__":
    try:
        test_all_json()
        test_json_output()
        print("\n🎉 All smoke tests passed!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Smoke test failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
