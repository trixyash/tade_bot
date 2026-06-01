"""
cli.py
------
Command-line interface for the Binance Futures Testnet Trading Bot.

Two modes:
  1. `place`       — Direct mode: supply all flags at once
  2. `interactive` — Guided mode: step-by-step prompts with live validation

Enhanced UX via Rich: colored tables, spinners, banners, and clear feedback.
"""

import os
import sys
import time
from typing import Optional

import typer
from dotenv import load_dotenv
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from bot.client import BinanceClient, BinanceClientError
from bot.logging_config import setup_logging
from bot.orders import OrderManager
from bot.validators import ValidationError, validate_all

# ─── Bootstrap ────────────────────────────────────────────────────────────────

load_dotenv()
log_file = setup_logging()

app = typer.Typer(
    name="trading-bot",
    help="Binance Futures Testnet Trading Bot",
    add_completion=False,
    rich_markup_mode="rich",
    no_args_is_help=True,
)
console = Console()

# ─── Constants ────────────────────────────────────────────────────────────────

BANNER = """[bold cyan]
  ██████╗ ██╗███╗   ██╗ █████╗ ███╗   ██╗ ██████╗███████╗
  ██╔══██╗██║████╗  ██║██╔══██╗████╗  ██║██╔════╝██╔════╝
  ██████╔╝██║██╔██╗ ██║███████║██╔██╗ ██║██║     █████╗  
  ██╔══██╗██║██║╚██╗██║██╔══██║██║╚██╗██║██║     ██╔══╝  
  ██████╔╝██║██║ ╚████║██║  ██║██║ ╚████║╚██████╗███████╗
  ╚═════╝ ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚══════╝
[/bold cyan][bold white]       Futures Testnet Bot  ·  Primetrade.ai Assessment[/bold white]
"""

SIDE_STYLE = {"BUY": "bold green", "SELL": "bold red"}
STATUS_STYLE = {
    "FILLED": "bold green",
    "NEW": "bold yellow",
    "PARTIALLY_FILLED": "yellow",
    "CANCELED": "red",
    "REJECTED": "bold red",
    "EXPIRED": "dim",
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_client() -> BinanceClient:
    """Load API credentials from environment and return an authenticated client."""
    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()

    missing = []
    if not api_key:
        missing.append("BINANCE_API_KEY")
    if not api_secret:
        missing.append("BINANCE_API_SECRET")

    if missing:
        console.print()
        console.print(
            Panel(
                f"[bold red]Missing environment variable(s):[/bold red]\n"
                + "\n".join(f"  • {v}" for v in missing)
                + "\n\n[dim]Copy [bold].env.example[/bold] → [bold].env[/bold] "
                "and fill in your Testnet credentials.[/dim]",
                title="[red]❌  Configuration Error[/red]",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    return BinanceClient(api_key, api_secret)


def print_banner() -> None:
    console.print(BANNER)


def print_order_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float],
) -> None:
    """Render a formatted order summary table before confirmation."""
    table = Table(
        title="  📋  Order Summary",
        box=box.ROUNDED,
        border_style="yellow",
        title_style="bold yellow",
        show_header=True,
        header_style="bold dim",
        min_width=42,
    )
    table.add_column("Field", style="cyan", width=14)
    table.add_column("Value", style="white")

    side_style = SIDE_STYLE.get(side, "white")

    table.add_row("Symbol", f"[bold]{symbol}[/bold]")
    table.add_row("Side", f"[{side_style}]{side}[/{side_style}]")
    table.add_row("Order Type", order_type)
    table.add_row("Quantity", str(quantity))
    if price is not None:
        table.add_row("Limit Price", f"${price:,.4f}")
    else:
        table.add_row("Limit Price", "[dim]N/A (Market)[/dim]")

    console.print()
    console.print(table)


def print_order_response(response: dict) -> None:
    """Render a formatted response table after a successful order."""
    side = response.get("side", "")
    status = response.get("status", "")
    side_style = SIDE_STYLE.get(side, "white")
    status_style = STATUS_STYLE.get(status, "white")

    table = Table(
        title="  ✅  Order Confirmed",
        box=box.ROUNDED,
        border_style="green",
        title_style="bold green",
        show_header=True,
        header_style="bold dim",
        min_width=42,
    )
    table.add_column("Field", style="cyan", width=18)
    table.add_column("Value", style="white")

    avg_price = response.get("avgPrice", "0")
    avg_price_str = (
        f"${float(avg_price):,.4f}" if avg_price and float(avg_price) > 0
        else "[dim]Pending fill[/dim]"
    )

    table.add_row("Order ID", str(response.get("orderId", "N/A")))
    table.add_row("Symbol", response.get("symbol", "N/A"))
    table.add_row("Side", f"[{side_style}]{side}[/{side_style}]")
    table.add_row("Type", response.get("type", "N/A"))
    table.add_row(
        "Status",
        f"[{status_style}]{status}[/{status_style}]",
    )
    table.add_row("Ordered Qty", response.get("origQty", "N/A"))
    table.add_row("Executed Qty", response.get("executedQty", "N/A"))
    table.add_row("Avg Fill Price", avg_price_str)

    price_val = response.get("price", "0")
    if price_val and float(price_val) > 0:
        table.add_row("Limit Price", f"${float(price_val):,.4f}")

    table.add_row("Time in Force", response.get("timeInForce", "N/A"))

    console.print()
    console.print(table)


def run_order(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float],
    skip_confirm: bool = False,
) -> None:
    """
    Core order execution flow used by both `place` and `interactive` commands:
      1. Show order summary
      2. Confirm with user
      3. Spin + call API
      4. Print response
    """
    # Validate
    try:
        symbol, side, order_type, quantity, price = validate_all(
            symbol, side, order_type, quantity, price
        )
    except ValidationError as exc:
        console.print(
            Panel(
                f"[red]{exc}[/red]",
                title="[red]❌  Validation Error[/red]",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    # Summary
    print_order_summary(symbol, side, order_type, quantity, price)

    # Confirm
    if not skip_confirm:
        console.print()
        confirmed = Confirm.ask(
            "[bold yellow]⚠️  Place this order on Binance Testnet?[/bold yellow]"
        )
        if not confirmed:
            console.print(
                "\n[yellow]Order cancelled — no request was sent.[/yellow]\n"
            )
            raise typer.Exit(0)

    # Place order
    console.print()
    try:
        client = get_client()
        manager = OrderManager(client)

        with console.status(
            "[bold green]Connecting to Binance Testnet…[/bold green]",
            spinner="dots",
        ):
            time.sleep(0.4)   # brief pause so spinner is visible
            response = manager.place_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
            )

        print_order_response(response)
        console.print(
            f"\n[bold green]✅  Order placed successfully![/bold green]"
        )

    except BinanceClientError as exc:
        console.print(
            Panel(
                f"[red]{exc}[/red]",
                title="[red]❌  API Error[/red]",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    except Exception as exc:
        console.print(
            Panel(
                f"[red]Unexpected error: {exc}[/red]",
                title="[red]❌  Error[/red]",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    finally:
        console.print(f"\n[dim]📝  Log saved → {log_file}[/dim]\n")


# ─── Commands ─────────────────────────────────────────────────────────────────

@app.command("place")
def place(
    symbol: str = typer.Option(
        ...,
        "--symbol", "-s",
        help="Trading pair  [dim](e.g. BTCUSDT)[/dim]",
        show_default=False,
    ),
    side: str = typer.Option(
        ...,
        "--side",
        help="Order side  [dim](BUY | SELL)[/dim]",
        show_default=False,
    ),
    order_type: str = typer.Option(
        ...,
        "--type", "-t",
        help="Order type  [dim](MARKET | LIMIT)[/dim]",
        show_default=False,
    ),
    quantity: float = typer.Option(
        ...,
        "--quantity", "-q",
        help="Quantity to trade  [dim](e.g. 0.01)[/dim]",
        show_default=False,
    ),
    price: Optional[float] = typer.Option(
        None,
        "--price", "-p",
        help="Limit price  [dim](required for LIMIT orders)[/dim]",
        show_default=False,
    ),
    yes: bool = typer.Option(
        False,
        "--yes", "-y",
        help="Skip confirmation prompt",
    ),
):
    """
    [bold]Place an order directly via flags.[/bold]

    Examples:

      [green]# Market BUY[/green]
      python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

      [green]# Limit SELL[/green]
      python cli.py place --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.1 --price 3500
    """
    print_banner()
    run_order(symbol, side, order_type, quantity, price, skip_confirm=yes)


@app.command("interactive")
def interactive():
    """
    [bold]Launch guided interactive mode.[/bold]

    Step-by-step prompts with live validation — no flags needed.
    Great for first-time use or exploring order options.
    """
    print_banner()
    console.print(
        Panel(
            "[bold cyan]Welcome to Interactive Mode[/bold cyan]\n"
            "[dim]Answer each prompt below. Press [bold]Ctrl+C[/bold] at any time to exit.[/dim]",
            border_style="cyan",
        )
    )
    console.print()

    # ── Symbol ────────────────────────────────────────────────
    while True:
        symbol = Prompt.ask(
            "[cyan]📌 Symbol[/cyan]",
            default="BTCUSDT",
        ).strip().upper()
        try:
            from bot.validators import validate_symbol
            validate_symbol(symbol)
            break
        except ValidationError as e:
            console.print(f"  [red]⚠  {e}[/red]")

    # ── Side ──────────────────────────────────────────────────
    while True:
        side = Prompt.ask(
            "[cyan]↕  Side[/cyan]",
            choices=["BUY", "SELL"],
            default="BUY",
        ).strip().upper()
        try:
            from bot.validators import validate_side
            validate_side(side)
            break
        except ValidationError as e:
            console.print(f"  [red]⚠  {e}[/red]")

    # ── Order Type ────────────────────────────────────────────
    while True:
        order_type = Prompt.ask(
            "[cyan]📄 Order Type[/cyan]",
            choices=["MARKET", "LIMIT"],
            default="MARKET",
        ).strip().upper()
        try:
            from bot.validators import validate_order_type
            validate_order_type(order_type)
            break
        except ValidationError as e:
            console.print(f"  [red]⚠  {e}[/red]")

    # ── Quantity ──────────────────────────────────────────────
    while True:
        qty_input = Prompt.ask(
            "[cyan]🔢 Quantity[/cyan]",
            default="0.01",
        )
        try:
            from bot.validators import validate_quantity
            quantity = validate_quantity(qty_input)
            break
        except ValidationError as e:
            console.print(f"  [red]⚠  {e}[/red]")

    # ── Price (LIMIT only) ────────────────────────────────────
    price = None
    if order_type == "LIMIT":
        while True:
            price_input = Prompt.ask(
                "[cyan]💲 Limit Price[/cyan]",
            )
            try:
                from bot.validators import validate_price
                price = validate_price(price_input, "LIMIT")
                break
            except ValidationError as e:
                console.print(f"  [red]⚠  {e}[/red]")

    console.print()
    console.print(Rule("[dim]Order Details[/dim]"))
    run_order(symbol, side, order_type, quantity, price)


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted — no order placed.[/yellow]\n")
        sys.exit(0)
