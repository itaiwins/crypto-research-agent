"""
News fetching tool for cryptocurrency news.

This module provides functionality to fetch recent news articles about
cryptocurrencies using the CryptoPanic API (free tier) and RSS feeds
as a fallback.
"""

import httpx
import feedparser
from typing import Any
from datetime import datetime
import os


# HTTP headers to avoid being blocked by news sites
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

# CryptoPanic API (free tier, optional API key for more requests)
CRYPTOPANIC_API_URL = "https://cryptopanic.com/api/v1/posts/"

# RSS feed sources for crypto news (no API key needed)
RSS_FEEDS = {
    "cointelegraph": "https://cointelegraph.com/rss",
    "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "bitcoinmagazine": "https://bitcoinmagazine.com/feed",
}

# Google News RSS - more reliable fallback
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}+cryptocurrency&hl=en-US&gl=US&ceid=US:en"

# Mapping of tickers to search terms for better news matching
TICKER_TO_SEARCH_TERMS: dict[str, list[str]] = {
    "BTC": ["bitcoin", "btc"],
    "ETH": ["ethereum", "eth"],
    "SOL": ["solana", "sol"],
    "ADA": ["cardano", "ada"],
    "DOT": ["polkadot", "dot"],
    "DOGE": ["dogecoin", "doge"],
    "XRP": ["ripple", "xrp"],
    "AVAX": ["avalanche", "avax"],
    "MATIC": ["polygon", "matic"],
    "LINK": ["chainlink", "link"],
    "UNI": ["uniswap", "uni"],
    "ATOM": ["cosmos", "atom"],
    "ARB": ["arbitrum", "arb"],
    "OP": ["optimism"],
    "SUI": ["sui"],
    "NEAR": ["near protocol", "near"],
    "APT": ["aptos", "apt"],
}


def get_search_terms(ticker: str) -> list[str]:
    """
    Get search terms for a cryptocurrency ticker.

    Args:
        ticker: The cryptocurrency ticker symbol

    Returns:
        A list of search terms to use when filtering news
    """
    ticker_upper = ticker.upper()
    return TICKER_TO_SEARCH_TERMS.get(ticker_upper, [ticker.lower()])


def fetch_rss_with_httpx(feed_url: str) -> feedparser.FeedParserDict:
    """
    Fetch and parse an RSS feed using httpx with proper headers.

    This helps avoid being blocked by news sites that check User-Agent.

    Args:
        feed_url: The URL of the RSS feed

    Returns:
        A parsed feedparser.FeedParserDict
    """
    try:
        with httpx.Client(timeout=10.0, headers=HTTP_HEADERS) as client:
            response = client.get(feed_url)
            response.raise_for_status()
            return feedparser.parse(response.text)
    except Exception:
        # Fall back to direct feedparser if httpx fails
        return feedparser.parse(feed_url)


def fetch_from_google_news(ticker: str, max_articles: int = 5) -> list[dict[str, Any]]:
    """
    Fetch news from Google News RSS feed.

    This is the most reliable method as Google News aggregates from many sources.

    Args:
        ticker: The cryptocurrency ticker symbol
        max_articles: Maximum number of articles to return

    Returns:
        A list of news article dictionaries
    """
    search_terms = get_search_terms(ticker)
    # Use the first/main search term (usually the full name like "bitcoin")
    query = search_terms[0] if search_terms else ticker.lower()

    articles = []

    try:
        feed_url = GOOGLE_NEWS_RSS.format(query=query)
        feed = fetch_rss_with_httpx(feed_url)

        for entry in feed.entries[:max_articles]:
            # Parse the publication date
            pub_date = entry.get("published", entry.get("updated", ""))
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6]).isoformat()

            # Extract source from title (Google News format: "Title - Source")
            title = entry.get("title", "No title")
            source = "Google News"
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                if len(parts) == 2:
                    title, source = parts

            articles.append({
                "title": title,
                "url": entry.get("link", ""),
                "source": source,
                "published_at": pub_date,
                "description": entry.get("summary", entry.get("description", ""))[:300],
            })

    except Exception:
        pass

    return articles[:max_articles]


def fetch_from_rss_feeds(ticker: str, max_articles: int = 5) -> list[dict[str, Any]]:
    """
    Fetch news from RSS feeds and filter by cryptocurrency.

    This is a fallback method that doesn't require any API keys.

    Args:
        ticker: The cryptocurrency ticker symbol
        max_articles: Maximum number of articles to return

    Returns:
        A list of news article dictionaries
    """
    search_terms = get_search_terms(ticker)
    articles = []

    for source_name, feed_url in RSS_FEEDS.items():
        try:
            # Parse the RSS feed using httpx for better compatibility
            feed = fetch_rss_with_httpx(feed_url)

            for entry in feed.entries[:20]:  # Check first 20 entries from each feed
                # Get the title and description
                title = entry.get("title", "").lower()
                description = entry.get("description", entry.get("summary", "")).lower()

                # Check if any search term is in the title or description
                if any(term in title or term in description for term in search_terms):
                    # Parse the publication date
                    pub_date = entry.get("published", entry.get("updated", ""))
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6]).isoformat()

                    articles.append({
                        "title": entry.get("title", "No title"),
                        "url": entry.get("link", ""),
                        "source": source_name.capitalize(),
                        "published_at": pub_date,
                        "description": entry.get("description", entry.get("summary", ""))[:300],
                    })

                    if len(articles) >= max_articles:
                        break

            if len(articles) >= max_articles:
                break

        except Exception:
            # Silently continue if a feed fails
            continue

    return articles[:max_articles]


def fetch_from_cryptopanic(ticker: str, max_articles: int = 5) -> list[dict[str, Any]]:
    """
    Fetch news from CryptoPanic API.

    CryptoPanic provides curated crypto news with optional API key.

    Args:
        ticker: The cryptocurrency ticker symbol
        max_articles: Maximum number of articles to return

    Returns:
        A list of news article dictionaries
    """
    # Get API key from environment (optional)
    api_key = os.getenv("CRYPTOPANIC_API_KEY")

    params: dict[str, Any] = {
        "currencies": ticker.upper(),
        "kind": "news",
        "public": "true",
    }

    if api_key:
        params["auth_token"] = api_key

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(CRYPTOPANIC_API_URL, params=params)
            response.raise_for_status()
            data = response.json()

        articles = []
        for result in data.get("results", [])[:max_articles]:
            articles.append({
                "title": result.get("title", "No title"),
                "url": result.get("url", ""),
                "source": result.get("source", {}).get("title", "Unknown"),
                "published_at": result.get("published_at", ""),
                "description": result.get("title", ""),  # CryptoPanic doesn't provide descriptions
            })

        return articles

    except Exception:
        # Return empty list on failure, will fall back to RSS
        return []


def get_crypto_news(ticker: str, max_articles: int = 5) -> dict[str, Any]:
    """
    Fetch recent news articles about a cryptocurrency.

    This function tries multiple sources in order of reliability:
    1. Google News RSS (most reliable, no API key needed)
    2. CryptoPanic API (if API key is available)
    3. Crypto-specific RSS feeds

    Args:
        ticker: The cryptocurrency ticker symbol (e.g., 'BTC', 'ETH')
        max_articles: Maximum number of articles to return (default: 5)

    Returns:
        A dictionary containing news articles or an error message

    Example:
        >>> news = get_crypto_news("ETH", max_articles=3)
        >>> for article in news["articles"]:
        ...     print(article["title"])
    """
    try:
        articles = []

        # Try Google News first (most reliable)
        google_articles = fetch_from_google_news(ticker, max_articles)
        articles.extend(google_articles)

        # If we need more, try CryptoPanic
        if len(articles) < max_articles:
            cryptopanic_articles = fetch_from_cryptopanic(
                ticker,
                max_articles - len(articles)
            )
            articles.extend(cryptopanic_articles)

        # Fall back to crypto RSS feeds if we still need more
        if len(articles) < max_articles:
            rss_articles = fetch_from_rss_feeds(
                ticker,
                max_articles - len(articles)
            )
            articles.extend(rss_articles)

        if not articles:
            return {
                "success": True,
                "ticker": ticker.upper(),
                "articles": [],
                "message": f"No recent news found for {ticker.upper()}. This could be a less popular cryptocurrency.",
            }

        return {
            "success": True,
            "ticker": ticker.upper(),
            "article_count": len(articles),
            "articles": articles,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to fetch news: {str(e)}",
        }


def get_news_tool_definition() -> dict[str, Any]:
    """
    Get the tool definition for the news fetching tool.

    This is used by the Anthropic API to understand what the tool does
    and what parameters it accepts.

    Returns:
        A dictionary containing the tool definition in Anthropic's format
    """
    return {
        "name": "get_crypto_news",
        "description": (
            "Fetches recent news articles about a cryptocurrency from various sources "
            "including CryptoPanic and major crypto news RSS feeds. Returns article titles, "
            "URLs, sources, and publication dates."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": (
                        "The cryptocurrency ticker symbol (e.g., 'BTC' for Bitcoin, "
                        "'ETH' for Ethereum, 'SOL' for Solana)"
                    ),
                },
                "max_articles": {
                    "type": "integer",
                    "description": "Maximum number of news articles to fetch (default: 5)",
                    "default": 5,
                },
            },
            "required": ["ticker"],
        },
    }
