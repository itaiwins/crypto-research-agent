"""
Command-line interface for the Crypto Research Agent.

This module provides a beautiful CLI experience using Typer and Rich
for researching cryptocurrencies.
"""

import sys
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.table import Table
from rich.text import Text
from rich import box
from dotenv import load_dotenv

from .agent import CryptoResearchAgent
from .tools import get_crypto_price, get_crypto_news


# Load environment variables from .env file
load_dotenv()

# Initialize Rich console and Typer app
console = Console()
app = typer.Typer(
    name="crypto-research",
    help="AI-powered cryptocurrency research agent using Claude",
    add_completion=False,
)


def print_header() -> None:
    """Print the application header."""
    header_text = Text()
    header_text.append("Crypto Research Agent", style="bold cyan")
    header_text.append("\n")
    header_text.append("AI-Powered Cryptocurrency Analysis", style="dim")

    console.print(Panel(
        header_text,
        box=box.DOUBLE,
        padding=(1, 2),
        border_style="cyan",
    ))
    console.print()


def format_price(value: float | None) -> str:
    """Format a price value with proper formatting."""
    if value is None:
        return "N/A"
    if value >= 1:
        return f"${value:,.2f}"
    else:
        return f"${value:.6f}"


def format_percentage(value: float | None) -> Text:
    """Format a percentage value with color coding."""
    if value is None:
        return Text("N/A", style="dim")

    if value > 0:
        return Text(f"+{value:.2f}%", style="bold green")
    elif value < 0:
        return Text(f"{value:.2f}%", style="bold red")
    else:
        return Text(f"{value:.2f}%", style="yellow")


def format_large_number(value: float | None) -> str:
    """Format large numbers with K, M, B suffixes."""
    if value is None:
        return "N/A"

    if value >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:.2f}T"
    elif value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.2f}K"
    else:
        return f"${value:.2f}"


@app.command()
def research(
    ticker: str = typer.Argument(
        ...,
        help="Cryptocurrency ticker symbol (e.g., BTC, ETH, SOL)",
    ),
    detailed: bool = typer.Option(
        False,
        "--detailed",
        "-d",
        help="Provide more detailed analysis",
    ),
    show_raw: bool = typer.Option(
        False,
        "--raw",
        "-r",
        help="Show raw tool outputs before the report",
    ),
) -> None:
    """
    Research a cryptocurrency and generate an AI-powered analysis report.

    Examples:
        python -m src.cli research BTC
        python -m src.cli research ETH --detailed
        python -m src.cli research SOL -d --raw
    """
    print_header()

    ticker = ticker.upper()
    console.print(f"[bold]Researching:[/bold] [cyan]{ticker}[/cyan]")
    console.print()

    # Show loading spinner while researching
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        try:
            # Create the agent
            progress.add_task(description="Initializing agent...", total=None)
            agent = CryptoResearchAgent(detailed=detailed)

            # Run the research
            progress.tasks[0].description = "Fetching price data and news..."
            result = agent.research(ticker)

        except ValueError as e:
            console.print()
            console.print(Panel(
                f"[red]Configuration Error[/red]\n\n{str(e)}\n\n"
                "[dim]Make sure you have set the ANTHROPIC_API_KEY environment variable.[/dim]",
                title="Error",
                border_style="red",
            ))
            raise typer.Exit(1)
        except Exception as e:
            console.print()
            console.print(Panel(
                f"[red]Unexpected Error[/red]\n\n{str(e)}",
                title="Error",
                border_style="red",
            ))
            raise typer.Exit(1)

    # Display results
    if not result["success"]:
        console.print(Panel(
            f"[red]Research Failed[/red]\n\n{result.get('error', 'Unknown error')}",
            title="Error",
            border_style="red",
        ))
        raise typer.Exit(1)

    # Show raw tool outputs if requested
    if show_raw and result.get("tool_calls"):
        console.print(Panel(
            "\n".join([
                f"[cyan]{call['tool']}[/cyan]: {call['input']}"
                for call in result["tool_calls"]
            ]),
            title="Tools Called",
            border_style="dim",
        ))
        console.print()

    # Display the research report
    console.print(Panel(
        Markdown(result["report"]),
        title=f"Research Report: {ticker}",
        border_style="green",
        padding=(1, 2),
    ))

    # Footer
    console.print()
    console.print(
        f"[dim]Model: {result.get('model', 'unknown')} | "
        f"Tools used: {len(result.get('tool_calls', []))}[/dim]"
    )


@app.command()
def price(
    ticker: str = typer.Argument(
        ...,
        help="Cryptocurrency ticker symbol (e.g., BTC, ETH, SOL)",
    ),
) -> None:
    """
    Fetch and display current price data for a cryptocurrency.

    This command fetches data directly from CoinGecko without using the AI agent.

    Examples:
        python -m src.cli price BTC
        python -m src.cli price ETH
    """
    print_header()

    ticker = ticker.upper()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(description=f"Fetching price data for {ticker}...", total=None)
        data = get_crypto_price(ticker)

    if not data.get("success"):
        console.print(Panel(
            f"[red]Error[/red]: {data.get('error', 'Unknown error')}",
            border_style="red",
        ))
        raise typer.Exit(1)

    # Create price table
    table = Table(
        title=f"{data['name']} ({data['symbol']})",
        box=box.ROUNDED,
        show_header=False,
        border_style="cyan",
    )
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Current Price", format_price(data.get("current_price")))
    table.add_row("24h Change", format_percentage(data.get("price_change_24h")))
    table.add_row("7d Change", format_percentage(data.get("price_change_7d")))
    table.add_row("30d Change", format_percentage(data.get("price_change_30d")))
    table.add_row("", "")  # Separator
    table.add_row("24h High", format_price(data.get("high_24h")))
    table.add_row("24h Low", format_price(data.get("low_24h")))
    table.add_row("", "")  # Separator
    table.add_row("Market Cap", format_large_number(data.get("market_cap")))
    table.add_row("Market Cap Rank", f"#{data.get('market_cap_rank', 'N/A')}")
    table.add_row("24h Volume", format_large_number(data.get("volume_24h")))
    table.add_row("", "")  # Separator
    table.add_row("All-Time High", format_price(data.get("ath")))

    console.print(table)


@app.command()
def news(
    ticker: str = typer.Argument(
        ...,
        help="Cryptocurrency ticker symbol (e.g., BTC, ETH, SOL)",
    ),
    limit: int = typer.Option(
        5,
        "--limit",
        "-l",
        help="Maximum number of articles to fetch",
    ),
) -> None:
    """
    Fetch and display recent news for a cryptocurrency.

    This command fetches news directly without using the AI agent.

    Examples:
        python -m src.cli news BTC
        python -m src.cli news ETH --limit 10
    """
    print_header()

    ticker = ticker.upper()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(description=f"Fetching news for {ticker}...", total=None)
        data = get_crypto_news(ticker, limit)

    if not data.get("success"):
        console.print(Panel(
            f"[red]Error[/red]: {data.get('error', 'Unknown error')}",
            border_style="red",
        ))
        raise typer.Exit(1)

    articles = data.get("articles", [])

    if not articles:
        console.print(Panel(
            f"[yellow]No recent news found for {ticker}[/yellow]",
            border_style="yellow",
        ))
        return

    console.print(f"[bold]Recent News for {ticker}[/bold]")
    console.print()

    for i, article in enumerate(articles, 1):
        # Create a panel for each article
        article_text = Text()
        article_text.append(article.get("title", "No title"), style="bold")
        article_text.append("\n")
        article_text.append(f"Source: {article.get('source', 'Unknown')}", style="dim")

        if article.get("published_at"):
            article_text.append(f" | {article['published_at'][:10]}", style="dim")

        if article.get("url"):
            article_text.append(f"\n{article['url']}", style="cyan underline")

        console.print(Panel(
            article_text,
            title=f"[{i}]",
            border_style="blue",
        ))


@app.command()
def supported() -> None:
    """
    List all supported cryptocurrency tickers.

    Shows the predefined ticker symbols that have optimized search mappings.
    """
    print_header()

    from .tools.price import TICKER_TO_ID

    table = Table(
        title="Supported Cryptocurrencies",
        box=box.ROUNDED,
        border_style="cyan",
    )
    table.add_column("Ticker", style="bold cyan")
    table.add_column("CoinGecko ID", style="dim")

    for ticker, coin_id in sorted(TICKER_TO_ID.items()):
        table.add_row(ticker, coin_id)

    console.print(table)
    console.print()
    console.print(
        "[dim]Note: Other tickers may also work but might have less accurate news matching.[/dim]"
    )


def main() -> None:
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
