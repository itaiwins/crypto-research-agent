"""
Tools module for the Crypto Research Agent.

Contains individual tools that the agent can use:
- price: Fetch cryptocurrency price data from CoinGecko
- news: Fetch recent news about cryptocurrencies
"""

from .price import get_crypto_price, get_price_tool_definition
from .news import get_crypto_news, get_news_tool_definition

__all__ = [
    "get_crypto_price",
    "get_price_tool_definition",
    "get_crypto_news",
    "get_news_tool_definition",
]
