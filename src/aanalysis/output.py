"""Output formatting for different formats."""

import csv
import json
import sys
from io import StringIO
from typing import Any, Optional

from rich.console import Console
from rich.table import Table

from aanalysis.digest import (
    get_agentic_index,
    get_coding_index,
    get_cost_per_intel_task,
    get_input_price,
    get_intelligence_index,
    get_output_price,
    get_time_to_first_token,
    get_tokens_per_second,
)


def is_tty() -> bool:
    """Check if stdout is a TTY."""
    return sys.stdout.isatty()


def format_number(value: Optional[float], precision: int = 2) -> str:
    """Format number with precision or '-' if None."""
    if value is None:
        return "-"
    return f"{value:.{precision}f}"


def format_usd(value: Optional[float]) -> str:
    """Format USD price or '-' if None."""
    if value is None:
        return "-"
    if value < 0.01:
        return f"${value:.4f}"
    return f"${value:.2f}"


def output_json(data: Any, compact: bool = False):
    """Output JSON."""
    if compact:
        print(json.dumps(data, separators=(',', ':')))
    else:
        print(json.dumps(data, indent=2))


def select_fields(items: list[dict[str, Any]], fields: list[str]) -> list[dict[str, Any]]:
    """Project selected fields from items."""
    return [
        {field: item.get(field) for field in fields}
        for item in items
    ]


def output_csv(items: list[dict[str, Any]], fields: Optional[list[str]] = None):
    """Output CSV."""
    if not items:
        return
    
    # Auto-detect fields if not specified
    if not fields:
        fields = list(items[0].keys())
    
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(items)
    print(output.getvalue().strip())


def build_model_table_data(models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build table data from models with enriched metrics."""
    rows = []
    for i, model in enumerate(models, 1):
        # Extract creator name from object
        creator = model.get("model_creator", {})
        if isinstance(creator, dict):
            creator_name = creator.get("name", "?")
        else:
            creator_name = model.get("model_creator_name", "?")
        
        row = {
            "rank": i,
            "id": model.get("id"),
            "slug": model.get("slug"),
            "name": model.get("name", "?"),
            "creator": creator_name,
            "intelligence_index": get_intelligence_index(model),
            "coding_index": get_coding_index(model),
            "agentic_index": get_agentic_index(model),
            "tokens_per_second": get_tokens_per_second(model),
            "time_to_first_token_s": get_time_to_first_token(model),
            "input_price_per_1m": get_input_price(model),
            "output_price_per_1m": get_output_price(model),
            "cost_per_intel_task": get_cost_per_intel_task(model),
            "open_guess": model.get("_open_guess"),
            "pareto_intel_speed": model.get("_pareto_intel_speed"),
        }
        rows.append(row)
    return rows


def output_models_table(
    models: list[dict[str, Any]],
    title: str = "Models",
    show_open: bool = False,
    show_pareto: bool = False
):
    """Output models as a rich table."""
    if not models:
        print(f"No models found for {title}")
        return
    
    console = Console()
    table = Table(title=title, show_header=True, header_style="bold cyan")
    
    # Core columns
    table.add_column("Rank", justify="right", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Creator")
    table.add_column("Intel", justify="right")
    table.add_column("Coding", justify="right")
    table.add_column("Tok/s", justify="right")
    table.add_column("TTFT(s)", justify="right")
    table.add_column("$/1M In", justify="right")
    table.add_column("$/1M Out", justify="right")
    table.add_column("$/Task", justify="right")
    
    if show_open:
        table.add_column("Open?", justify="center")
    
    if show_pareto:
        table.add_column("Pareto", justify="center")
    
    for i, model in enumerate(models, 1):
        # Extract creator name
        creator = model.get("model_creator", {})
        if isinstance(creator, dict):
            creator_name = creator.get("name", "?")
        else:
            creator_name = model.get("model_creator_name", "?")
        
        row = [
            str(i),
            model.get("name", "?"),
            creator_name,
            format_number(get_intelligence_index(model), 1),
            format_number(get_coding_index(model), 1),
            format_number(get_tokens_per_second(model), 0),
            format_number(get_time_to_first_token(model), 2),
            format_usd(get_input_price(model)),
            format_usd(get_output_price(model)),
            format_usd(get_cost_per_intel_task(model)),
        ]
        
        if show_open:
            open_guess = model.get("_open_guess")
            row.append("✓" if open_guess else "✗")
        
        if show_pareto:
            pareto = model.get("_pareto_intel_speed")
            row.append("🌟" if pareto else "")
        
        table.add_row(*row)
    
    console.print(table)
    console.print()


def output_attribution():
    """Output Artificial Analysis attribution footer."""
    console = Console()
    console.print("[dim]Data provided by Artificial Analysis (artificialanalysis.ai)[/dim]")
    console.print()


def output_models(
    models: list[dict[str, Any]],
    title: str = "Models",
    output_format: str = "auto",
    compact: bool = False,
    select: Optional[list[str]] = None,
    show_open: bool = False,
    show_pareto: bool = False
):
    """Output models in requested format.
    
    Args:
        models: List of models
        title: Table title for human output
        output_format: "auto", "json", "csv", or "table"
        compact: Compact JSON output
        select: Fields to project
        show_open: Show open-weight guess column
        show_pareto: Show Pareto frontier marker
    """
    if not models:
        if output_format in ("auto", "table") and is_tty():
            print(f"No models found for {title}")
        else:
            output_json([])
        return
    
    # Determine output format
    if output_format == "auto":
        output_format = "table" if is_tty() else "json"
    
    # Build enriched table data
    table_data = build_model_table_data(models)
    
    # Project fields if requested
    if select:
        table_data = select_fields(table_data, select)
    
    # Output
    if output_format == "json":
        output_json(table_data, compact=compact)
    elif output_format == "csv":
        output_csv(table_data)
    else:  # table
        output_models_table(models, title=title, show_open=show_open, show_pareto=show_pareto)
        output_attribution()
