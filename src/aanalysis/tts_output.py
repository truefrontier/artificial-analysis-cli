"""Output formatting for TTS models."""

from typing import Any, Optional

from aanalysis.output import format_number, format_usd, is_tty, output_json, select_fields, output_csv
from aanalysis.tts_digest import (
    get_elo,
    get_ci95,
    get_rank,
    get_price_per_1m_chars,
    get_chars_per_second,
)

from rich.console import Console
from rich.table import Table


def build_tts_table_data(models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build table data from TTS models with enriched metrics."""
    rows = []
    for i, model in enumerate(models, 1):
        # Extract creator name from object
        creator = model.get("model_creator", {})
        if isinstance(creator, dict):
            creator_name = creator.get("name", "?")
        else:
            creator_name = model.get("model_creator_name", "?")
        
        row = {
            "rank": model.get("rank") or i,
            "id": model.get("id", "?"),
            "slug": model.get("slug", "?"),
            "name": model.get("name", "?"),
            "creator": creator_name,
            "elo": get_elo(model),
            "ci95": get_ci95(model),
            "price_per_1m_chars": get_price_per_1m_chars(model),
            "chars_per_second": get_chars_per_second(model),
        }
        rows.append(row)
    return rows


def output_tts_table(
    models: list[dict[str, Any]],
    title: str = "TTS Models",
    show_price: bool = False,
    show_speed: bool = False
):
    """Output TTS models as a rich table."""
    if not models:
        print(f"No TTS models found for {title}")
        return
    
    console = Console()
    table = Table(title=title, show_header=True, header_style="bold cyan")
    
    # Core columns
    table.add_column("Rank", justify="right", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Creator")
    table.add_column("Elo", justify="right")
    table.add_column("CI95", justify="right")
    
    if show_price:
        table.add_column("$/1M chars", justify="right")
    
    if show_speed:
        table.add_column("chars/s", justify="right")
    
    for model in models:
        # Extract creator name
        creator = model.get("model_creator", {})
        if isinstance(creator, dict):
            creator_name = creator.get("name", "?")
        else:
            creator_name = model.get("model_creator_name", "?")
        
        rank = model.get("rank")
        if rank is None:
            # Use position in list
            rank = models.index(model) + 1
        
        row = [
            str(rank),
            model.get("name", "?"),
            creator_name,
            format_number(get_elo(model), 1),
            format_number(get_ci95(model), 1),
        ]
        
        if show_price:
            row.append(format_usd(get_price_per_1m_chars(model)))
        
        if show_speed:
            row.append(format_number(get_chars_per_second(model), 0))
        
        table.add_row(*row)
    
    console.print(table)
    console.print()


def output_tts_models(
    models: list[dict[str, Any]],
    title: str = "TTS Models",
    output_format: str = "auto",
    compact: bool = False,
    select: Optional[list[str]] = None,
    show_price: bool = False,
    show_speed: bool = False
):
    """Output TTS models in requested format.
    
    Args:
        models: List of TTS models
        title: Table title for human output
        output_format: "auto", "json", "csv", or "table"
        compact: Compact JSON output
        select: Fields to project
        show_price: Show price column in table
        show_speed: Show speed column in table
    """
    if not models:
        if output_format in ("auto", "table") and is_tty():
            print(f"No TTS models found for {title}")
        else:
            output_json([])
        return
    
    # Determine output format
    if output_format == "auto":
        output_format = "table" if is_tty() else "json"
    
    # Build enriched table data
    table_data = build_tts_table_data(models)
    
    # Project fields if requested
    if select:
        table_data = select_fields(table_data, select)
    
    # Output
    if output_format == "json":
        output_json(table_data, compact=compact)
    elif output_format == "csv":
        output_csv(table_data)
    else:  # table
        output_tts_table(models, title=title, show_price=show_price, show_speed=show_speed)
        from aanalysis.output import output_attribution
        output_attribution()
