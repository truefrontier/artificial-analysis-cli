"""CLI application."""

import sys
from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from aanalysis import __version__
from aanalysis.client import ArtificialAnalysisClient, AuthError, APIError
from aanalysis.config import read_api_key_from_file, read_api_key_from_stdin, set_api_key
from aanalysis.digest import (
    filter_models,
    get_open_digest,
    normalize_model,
    pick_recommendation,
    rank_by_coding,
    rank_by_intelligence,
    rank_by_smart_cheap,
    rank_by_smart_fast,
)
from aanalysis.output import output_attribution, output_json, output_models, output_models_table

app = typer.Typer(
    name="aanalysis",
    help="Read-only CLI for Artificial Analysis LLM data",
    no_args_is_help=True,
    add_completion=False,
)

config_app = typer.Typer(help="Configuration commands")
app.add_typer(config_app, name="config")

models_app = typer.Typer(help="Model listing commands")
app.add_typer(models_app, name="models")

digest_app = typer.Typer(help="Digest commands")
app.add_typer(digest_app, name="digest")


# Global options
class GlobalOptions:
    """Global CLI options."""
    json_output: bool = False
    compact: bool = False
    select_fields: Optional[list[str]] = None
    csv_output: bool = False
    quiet: bool = False


global_opts = GlobalOptions()


def get_output_format() -> str:
    """Determine output format from global options."""
    if global_opts.json_output:
        return "json"
    if global_opts.csv_output:
        return "csv"
    return "auto"


def handle_api_error(e: Exception):
    """Handle API errors with appropriate exit codes."""
    if isinstance(e, AuthError):
        if not global_opts.quiet:
            print(f"Error: {e}", file=sys.stderr)
            print("Configure API key with: aanalysis config set-key", file=sys.stderr)
        sys.exit(4)
    elif isinstance(e, APIError):
        if not global_opts.quiet:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(4)
    else:
        if not global_opts.quiet:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


@app.command()
def version():
    """Show version."""
    print(f"aanalysis {__version__}")


@config_app.command("set-key")
def config_set_key(
    key_file: Annotated[
        Optional[Path],
        typer.Option("--key-file", help="Read key from file instead of stdin")
    ] = None
):
    """Set API key (reads from stdin or --key-file)."""
    try:
        if key_file:
            key = read_api_key_from_file(key_file)
        else:
            key = read_api_key_from_stdin()
        
        set_api_key(key)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(3)


@models_app.command("list")
def models_list(
    limit: Annotated[Optional[int], typer.Option(help="Limit number of results")] = None,
    creator: Annotated[Optional[str], typer.Option(help="Filter by creator")] = None,
    min_intel: Annotated[Optional[float], typer.Option("--min-intel", help="Minimum intelligence index")] = None,
    refresh: Annotated[bool, typer.Option("--refresh", help="Bust cache")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output JSON")] = False,
    compact: Annotated[bool, typer.Option("--compact", help="Compact JSON")] = False,
    select: Annotated[Optional[str], typer.Option("--select", help="Select fields (comma-separated)")] = None,
    csv_output: Annotated[bool, typer.Option("--csv", help="Output CSV")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", help="Quiet mode")] = False,
):
    """List LLM models."""
    # Set global options
    global_opts.json_output = json_output
    global_opts.compact = compact
    global_opts.csv_output = csv_output
    global_opts.quiet = quiet
    if select:
        global_opts.select_fields = [f.strip() for f in select.split(",")]
    
    try:
        client = ArtificialAnalysisClient()
        models = client.fetch_all_models(refresh=refresh)
        
        # Normalize models
        models = [normalize_model(m) for m in models]
        
        # Apply filters
        models = filter_models(models, creator=creator, min_intelligence=min_intel)
        
        # Sort by intelligence by default
        models = rank_by_intelligence(models, limit=limit)
        
        # Output
        output_models(
            models,
            title="LLM Models",
            output_format=get_output_format(),
            compact=compact,
            select=global_opts.select_fields
        )
        
    except Exception as e:
        handle_api_error(e)


@digest_app.command("smartest")
def digest_smartest(
    limit: Annotated[int, typer.Option(help="Limit number of results")] = 10,
    refresh: Annotated[bool, typer.Option("--refresh", help="Bust cache")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output JSON")] = False,
    compact: Annotated[bool, typer.Option("--compact", help="Compact JSON")] = False,
    select: Annotated[Optional[str], typer.Option("--select", help="Select fields (comma-separated)")] = None,
    csv_output: Annotated[bool, typer.Option("--csv", help="Output CSV")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", help="Quiet mode")] = False,
):
    """Top models by intelligence index."""
    # Set global options
    global_opts.json_output = json_output
    global_opts.compact = compact
    global_opts.csv_output = csv_output
    global_opts.quiet = quiet
    if select:
        global_opts.select_fields = [f.strip() for f in select.split(",")]
    
    try:
        client = ArtificialAnalysisClient()
        models = client.fetch_all_models(refresh=refresh)
        models = [normalize_model(m) for m in models]
        
        ranked = rank_by_intelligence(models, limit=limit)
        
        output_models(
            ranked,
            title=f"Top {limit} Smartest Models",
            output_format=get_output_format(),
            compact=compact,
            select=global_opts.select_fields
        )
        
    except Exception as e:
        handle_api_error(e)


@digest_app.command("smart-fast")
def digest_smart_fast(
    limit: Annotated[int, typer.Option(help="Limit number of results")] = 10,
    refresh: Annotated[bool, typer.Option("--refresh", help="Bust cache")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output JSON")] = False,
    compact: Annotated[bool, typer.Option("--compact", help="Compact JSON")] = False,
    select: Annotated[Optional[str], typer.Option("--select", help="Select fields (comma-separated)")] = None,
    csv_output: Annotated[bool, typer.Option("--csv", help="Output CSV")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", help="Quiet mode")] = False,
):
    """Top models by intelligence + speed composite (Pareto frontier marked)."""
    # Set global options
    global_opts.json_output = json_output
    global_opts.compact = compact
    global_opts.csv_output = csv_output
    global_opts.quiet = quiet
    if select:
        global_opts.select_fields = [f.strip() for f in select.split(",")]
    
    try:
        client = ArtificialAnalysisClient()
        models = client.fetch_all_models(refresh=refresh)
        models = [normalize_model(m) for m in models]
        
        ranked = rank_by_smart_fast(models, limit=limit)
        
        output_models(
            ranked,
            title=f"Top {limit} Smart & Fast Models",
            output_format=get_output_format(),
            compact=compact,
            select=global_opts.select_fields,
            show_pareto=True
        )
        
    except Exception as e:
        handle_api_error(e)


@digest_app.command("smart-cheap")
def digest_smart_cheap(
    limit: Annotated[int, typer.Option(help="Limit number of results")] = 10,
    refresh: Annotated[bool, typer.Option("--refresh", help="Bust cache")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output JSON")] = False,
    compact: Annotated[bool, typer.Option("--compact", help="Compact JSON")] = False,
    select: Annotated[Optional[str], typer.Option("--select", help="Select fields (comma-separated)")] = None,
    csv_output: Annotated[bool, typer.Option("--csv", help="Output CSV")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", help="Quiet mode")] = False,
):
    """Top models by cost efficiency (low cost per intelligence)."""
    # Set global options
    global_opts.json_output = json_output
    global_opts.compact = compact
    global_opts.csv_output = csv_output
    global_opts.quiet = quiet
    if select:
        global_opts.select_fields = [f.strip() for f in select.split(",")]
    
    try:
        client = ArtificialAnalysisClient()
        models = client.fetch_all_models(refresh=refresh)
        models = [normalize_model(m) for m in models]
        
        ranked = rank_by_smart_cheap(models, limit=limit)
        
        output_models(
            ranked,
            title=f"Top {limit} Smart & Cheap Models",
            output_format=get_output_format(),
            compact=compact,
            select=global_opts.select_fields
        )
        
    except Exception as e:
        handle_api_error(e)


@digest_app.command("open")
def digest_open(
    limit: Annotated[int, typer.Option(help="Limit number of results")] = 10,
    refresh: Annotated[bool, typer.Option("--refresh", help="Bust cache")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output JSON")] = False,
    compact: Annotated[bool, typer.Option("--compact", help="Compact JSON")] = False,
    select: Annotated[Optional[str], typer.Option("--select", help="Select fields (comma-separated)")] = None,
    csv_output: Annotated[bool, typer.Option("--csv", help="Output CSV")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", help="Quiet mode")] = False,
):
    """Top open-weight models (heuristic guess) + gap vs proprietary."""
    # Set global options
    global_opts.json_output = json_output
    global_opts.compact = compact
    global_opts.csv_output = csv_output
    global_opts.quiet = quiet
    if select:
        global_opts.select_fields = [f.strip() for f in select.split(",")]
    
    try:
        client = ArtificialAnalysisClient()
        models = client.fetch_all_models(refresh=refresh)
        models = [normalize_model(m) for m in models]
        
        digest = get_open_digest(models, limit=limit)
        
        if json_output or csv_output:
            # JSON/CSV output: just the open models with open_guess field
            output_models(
                digest["open_models"],
                title=f"Top {limit} Open-Weight Models",
                output_format=get_output_format(),
                compact=compact,
                select=global_opts.select_fields,
                show_open=True
            )
        else:
            # Human output: show both lists
            output_models_table(
                digest["open_models"],
                title=f"Top {limit} Open-Weight Models (Heuristic)",
                show_open=True
            )
            
            print("\nTop 5 Proprietary Models for Comparison:\n")
            output_models_table(
                digest["proprietary_comparison"],
                title="Top Proprietary Models",
                show_open=True
            )
            
            if digest["intelligence_gap"] is not None:
                print(f"Intelligence gap (proprietary - open): {digest['intelligence_gap']:.1f}\n")
            
            output_attribution()
        
    except Exception as e:
        handle_api_error(e)


@digest_app.command("coding")
def digest_coding(
    limit: Annotated[int, typer.Option(help="Limit number of results")] = 10,
    refresh: Annotated[bool, typer.Option("--refresh", help="Bust cache")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output JSON")] = False,
    compact: Annotated[bool, typer.Option("--compact", help="Compact JSON")] = False,
    select: Annotated[Optional[str], typer.Option("--select", help="Select fields (comma-separated)")] = None,
    csv_output: Annotated[bool, typer.Option("--csv", help="Output CSV")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", help="Quiet mode")] = False,
):
    """Top models for coding (coding index when present, else intelligence)."""
    # Set global options
    global_opts.json_output = json_output
    global_opts.compact = compact
    global_opts.csv_output = csv_output
    global_opts.quiet = quiet
    if select:
        global_opts.select_fields = [f.strip() for f in select.split(",")]
    
    try:
        client = ArtificialAnalysisClient()
        models = client.fetch_all_models(refresh=refresh)
        models = [normalize_model(m) for m in models]
        
        ranked = rank_by_coding(models, limit=limit)
        
        output_models(
            ranked,
            title=f"Top {limit} Coding Models",
            output_format=get_output_format(),
            compact=compact,
            select=global_opts.select_fields
        )
        
    except Exception as e:
        handle_api_error(e)


@digest_app.command("pick")
def digest_pick(
    category: Annotated[
        str,
        typer.Argument(help="Category: local, cheap-api, frontier, or coding-agent")
    ],
    refresh: Annotated[bool, typer.Option("--refresh", help="Bust cache")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output JSON")] = False,
    compact: Annotated[bool, typer.Option("--compact", help="Compact JSON")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", help="Quiet mode")] = False,
):
    """Pick one clear recommendation + runners-up for a category."""
    # Set global options
    global_opts.json_output = json_output
    global_opts.compact = compact
    global_opts.quiet = quiet
    
    valid_categories = ["local", "cheap-api", "frontier", "coding-agent"]
    if category not in valid_categories:
        print(f"Error: Invalid category '{category}'. Choose from: {', '.join(valid_categories)}", file=sys.stderr)
        sys.exit(3)
    
    try:
        client = ArtificialAnalysisClient()
        models = client.fetch_all_models(refresh=refresh)
        models = [normalize_model(m) for m in models]
        
        result = pick_recommendation(models, category)
        
        if json_output:
            output_json(result, compact=compact)
        else:
            # Human output
            print(f"\n📍 Recommendation for '{category}':\n")
            if result["recommendation"]:
                rec = result["recommendation"]
                print(f"  → {rec.get('name', '?')} by {rec.get('model_creator', '?')}")
                
                from aanalysis.digest import get_intelligence_index, get_coding_index
                intel = get_intelligence_index(rec)
                coding = get_coding_index(rec)
                if intel:
                    print(f"    Intelligence: {intel:.1f}")
                if coding:
                    print(f"    Coding: {coding:.1f}")
            else:
                print("  No recommendation found")
            
            if result["runners_up"]:
                print("\n  Runners-up:")
                for i, model in enumerate(result["runners_up"], 2):
                    print(f"    {i}. {model.get('name', '?')} by {model.get('model_creator', '?')}")
            
            print()
            output_attribution()
        
    except Exception as e:
        handle_api_error(e)


@digest_app.command("all")
def digest_all(
    limit: Annotated[int, typer.Option(help="Limit per digest")] = 5,
    refresh: Annotated[bool, typer.Option("--refresh", help="Bust cache")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output JSON")] = False,
    compact: Annotated[bool, typer.Option("--compact", help="Compact JSON")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", help="Quiet mode")] = False,
):
    """Run all main digests in one agent-friendly payload."""
    # Set global options
    global_opts.json_output = json_output
    global_opts.compact = compact
    global_opts.quiet = quiet
    
    try:
        client = ArtificialAnalysisClient()
        models = client.fetch_all_models(refresh=refresh)
        models = [normalize_model(m) for m in models]
        
        # Generate all digests
        from aanalysis.digest import get_open_digest
        from aanalysis.output import build_model_table_data
        
        all_digests = {
            "smartest": build_model_table_data(rank_by_intelligence(models, limit=limit)),
            "smart_fast": build_model_table_data(rank_by_smart_fast(models, limit=limit)),
            "smart_cheap": build_model_table_data(rank_by_smart_cheap(models, limit=limit)),
            "coding": build_model_table_data(rank_by_coding(models, limit=limit)),
            "open": build_model_table_data(get_open_digest(models, limit=limit)["open_models"]),
            "picks": {
                "local": pick_recommendation(models, "local"),
                "cheap_api": pick_recommendation(models, "cheap-api"),
                "frontier": pick_recommendation(models, "frontier"),
                "coding_agent": pick_recommendation(models, "coding-agent"),
            }
        }
        
        output_json(all_digests, compact=compact)
        
    except Exception as e:
        handle_api_error(e)


if __name__ == "__main__":
    app()
