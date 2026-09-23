#!/usr/bin/env python3
"""Demo script showing aanalysis CLI with fixture data."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

# Mock the client to return fixture data
def mock_fetch_all_models(self, refresh=False):
    """Mock fetch that returns fixture data."""
    fixture_path = Path(__file__).parent / "tests" / "fixtures" / "models.json"
    data = json.loads(fixture_path.read_text())
    return data["models"]


def run_command(args):
    """Run aanalysis command."""
    cmd = ["python3", "-m", "aanalysis.cli"] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
    return result


def demo():
    """Run demo commands."""
    # Patch the client
    import sys
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    
    from aanalysis import client
    original_method = client.ArtificialAnalysisClient.fetch_all_models
    client.ArtificialAnalysisClient.fetch_all_models = mock_fetch_all_models
    
    try:
        print("=" * 70)
        print("DEMO: aanalysis digest all --json")
        print("=" * 70)
        print()
        
        result = run_command(["digest", "all", "--json", "--limit", "3"])
        if result.returncode == 0:
            output = json.loads(result.stdout)
            print(json.dumps(output, indent=2))
            print("\n✓ Success!")
        else:
            print(f"Error (exit {result.returncode}):")
            print(result.stderr)
        
        print("\n" + "=" * 70)
        print("DEMO: aanalysis digest pick frontier")
        print("=" * 70)
        print()
        
        result = run_command(["digest", "pick", "frontier"])
        if result.returncode == 0:
            print(result.stdout)
            print("✓ Success!")
        else:
            print(f"Error (exit {result.returncode}):")
            print(result.stderr)
            
    finally:
        # Restore original
        client.ArtificialAnalysisClient.fetch_all_models = original_method


if __name__ == "__main__":
    demo()
