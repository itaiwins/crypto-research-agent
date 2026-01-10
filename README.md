# Crypto Research Agent

> **An AI agent that researches cryptocurrencies using Claude's tool-use capabilities**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Anthropic API](https://img.shields.io/badge/Anthropic-Claude-orange.svg)](https://www.anthropic.com/)

This project demonstrates the **agentic AI pattern** - where an LLM (Claude) acts as a reasoning engine that can autonomously decide which tools to use, execute them, and synthesize results into a coherent output.

**Built for my AI Engineer portfolio**

---

## Quick Demo

```bash
# Check real-time price (no API key needed)
python -m src.cli price BTC

# Get recent news (no API key needed)
python -m src.cli news ETH --limit 3

# Generate AI research report (requires Anthropic API key)
python -m src.cli research SOL
```

## Features

- **Real-time Price Data**: Fetches current prices, 24h/7d/30d changes, market cap, and volume from CoinGecko
- **News Aggregation**: Gathers recent news from multiple sources (CryptoPanic, RSS feeds)
- **AI-Powered Analysis**: Uses Claude to synthesize data into professional research briefs
- **Beautiful CLI**: Rich terminal output with colors, panels, and formatting
- **Tool-Use Architecture**: Demonstrates Claude's function calling capabilities
- **30+ Cryptocurrencies**: Pre-configured support for major coins (BTC, ETH, SOL, and more)

## Architecture

This project demonstrates an **agentic AI architecture** where Claude acts as the reasoning engine and orchestrates various tools to complete research tasks:

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Request                              │
│                    "Research BTC"                                │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Claude Agent                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  1. Analyze request                                      │    │
│  │  2. Decide which tools to use                            │    │
│  │  3. Call tools and process results                       │    │
│  │  4. Synthesize into research brief                       │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────┬───────────────────────────────────────────┘
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  Price Tool     │     │   News Tool     │
│  (CoinGecko)    │     │ (CryptoPanic/   │
│                 │     │  RSS Feeds)     │
└─────────────────┘     └─────────────────┘
```

### How It Works

1. **User Input**: You provide a cryptocurrency ticker (e.g., "BTC")
2. **Agent Planning**: Claude analyzes the request and decides to fetch price data and news
3. **Tool Execution**: The agent calls the appropriate tools:
   - `get_crypto_price`: Fetches real-time data from CoinGecko API
   - `get_crypto_news`: Aggregates news from multiple sources
4. **Synthesis**: Claude analyzes all gathered data and generates a professional research brief
5. **Output**: Beautiful formatted output in your terminal

## Installation

### Prerequisites

- Python 3.10 or higher
- An Anthropic API key ([get one here](https://console.anthropic.com/))

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/itaiwins/crypto-research-agent.git
   cd crypto-research-agent
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your Anthropic API key
   ```

## Usage

### Research a Cryptocurrency

Generate a comprehensive AI-powered research brief:

```bash
# Basic research
python -m src.cli research BTC

# Detailed analysis
python -m src.cli research ETH --detailed

# Show raw tool outputs
python -m src.cli research SOL --raw
```

### Quick Price Check

Get current price data without AI analysis:

```bash
python -m src.cli price BTC
python -m src.cli price ETH
```

### Fetch News

Get recent news for a cryptocurrency:

```bash
python -m src.cli news BTC
python -m src.cli news ETH --limit 10
```

### List Supported Cryptocurrencies

```bash
python -m src.cli supported
```

## Example Output

```
╔════════════════════════════════════════════════════════════════╗
║              Crypto Research Agent                              ║
║        AI-Powered Cryptocurrency Analysis                       ║
╚════════════════════════════════════════════════════════════════╝

Researching: BTC

╭─────────────────── Research Report: BTC ────────────────────────╮
│                                                                  │
│  ## Price Analysis                                               │
│                                                                  │
│  Bitcoin (BTC) is currently trading at **$67,234.56**, showing   │
│  a **+2.34%** gain over the past 24 hours. The weekly change     │
│  stands at **+5.67%**, indicating sustained bullish momentum.    │
│                                                                  │
│  ## Market Overview                                              │
│                                                                  │
│  - **Market Cap**: $1.32T (Rank #1)                              │
│  - **24h Volume**: $28.5B                                        │
│  - **Circulating Supply**: 19.6M BTC                             │
│                                                                  │
│  ## News Summary                                                 │
│                                                                  │
│  Recent developments include institutional adoption news and     │
│  regulatory updates. Key headlines focus on ETF inflows and      │
│  on-chain metrics showing accumulation patterns.                 │
│                                                                  │
│  ## Key Takeaways                                                │
│                                                                  │
│  • Strong price momentum with positive weekly performance        │
│  • High trading volume indicates active market participation     │
│  • News sentiment remains cautiously optimistic                  │
│                                                                  │
╰──────────────────────────────────────────────────────────────────╯
```

## Project Structure

```
crypto-research-agent/
├── src/
│   ├── __init__.py         # Package initialization
│   ├── __main__.py         # Module entry point
│   ├── agent.py            # 🧠 Main agent logic with Claude (START HERE)
│   ├── cli.py              # Command-line interface
│   └── tools/
│       ├── __init__.py     # Tools package
│       ├── price.py        # CoinGecko price fetching
│       └── news.py         # News aggregation
├── .env.example            # Example environment variables
├── .gitignore              # Git ignore rules
├── pyproject.toml          # Project configuration
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

### Key Files for Code Review

| File | Description | Lines of Code |
|------|-------------|---------------|
| [`src/agent.py`](src/agent.py) | **Core agentic loop** - Claude reasoning + tool orchestration | ~300 |
| [`src/tools/price.py`](src/tools/price.py) | CoinGecko API integration with error handling | ~120 |
| [`src/tools/news.py`](src/tools/news.py) | Multi-source news aggregation (Google News, RSS) | ~200 |
| [`src/cli.py`](src/cli.py) | Rich CLI with Typer | ~250 |

## API Keys

| Service | Required | Description |
|---------|----------|-------------|
| Anthropic | **Yes** | Powers the AI agent (Claude) |
| CryptoPanic | No | Optional, improves news results |

**Note**: CoinGecko's free API doesn't require an API key.

## Technologies Used

- **[Anthropic Claude](https://www.anthropic.com/)**: AI reasoning engine with tool use
- **[CoinGecko API](https://www.coingecko.com/en/api)**: Real-time cryptocurrency data
- **[Typer](https://typer.tiangolo.com/)**: Modern CLI framework
- **[Rich](https://rich.readthedocs.io/)**: Beautiful terminal formatting
- **[HTTPX](https://www.python-httpx.org/)**: Modern async HTTP client
- **[Feedparser](https://feedparser.readthedocs.io/)**: RSS feed parsing

## Future Improvements

- [ ] Add technical analysis indicators (RSI, MACD, etc.)
- [ ] Support for multiple currencies (EUR, GBP, etc.)
- [ ] Historical price chart generation
- [ ] Sentiment analysis from social media
- [ ] Portfolio tracking and alerts
- [ ] Web interface with Streamlit
- [ ] Async support for faster data fetching
- [ ] Caching layer to reduce API calls
- [ ] Support for more news sources
- [ ] Export reports to PDF/Markdown

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Anthropic](https://www.anthropic.com/) for Claude and the tool use API
- [CoinGecko](https://www.coingecko.com/) for the free cryptocurrency API
- [CryptoPanic](https://cryptopanic.com/) for the news API

---

**Disclaimer**: This tool is for educational and research purposes only. It does not provide financial advice. Always do your own research before making investment decisions.
