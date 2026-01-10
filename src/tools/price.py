"""
Price fetching tool using the CoinGecko API.

This module provides functionality to fetch real-time cryptocurrency
price data including current price, 24h change, market cap, and volume.
"""

import httpx
from typing import Any


# CoinGecko API base URL (free, no API key required)
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"

# Mapping of common ticker symbols to CoinGecko IDs
# CoinGecko uses full names as IDs, not ticker symbols
TICKER_TO_ID: dict[str, str] = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "ADA": "cardano",
    "DOT": "polkadot",
    "DOGE": "dogecoin",
    "XRP": "ripple",
    "AVAX": "avalanche-2",
    "MATIC": "matic-network",
    "LINK": "chainlink",
    "UNI": "uniswap",
    "ATOM": "cosmos",
    "LTC": "litecoin",
    "BCH": "bitcoin-cash",
    "ALGO": "algorand",
    "XLM": "stellar",
    "VET": "vechain",
    "FIL": "filecoin",
    "TRX": "tron",
    "ETC": "ethereum-classic",
    "NEAR": "near",
    "APT": "aptos",
    "ARB": "arbitrum",
    "OP": "optimism",
    "SUI": "sui",
    "SEI": "sei-network",
    "INJ": "injective-protocol",
    "TIA": "celestia",
    "PEPE": "pepe",
    "SHIB": "shiba-inu",
    "WIF": "dogwifcoin",
    "BONK": "bonk",
}


def get_coingecko_id(ticker: str) -> str:
    """
    Convert a ticker symbol to a CoinGecko ID.

    Args:
        ticker: The cryptocurrency ticker symbol (e.g., 'BTC', 'ETH')

    Returns:
        The CoinGecko ID for the cryptocurrency

    Note:
        If the ticker is not in the predefined mapping, it will be
        converted to lowercase and used as-is (may not always work).
    """
    ticker_upper = ticker.upper()
    return TICKER_TO_ID.get(ticker_upper, ticker.lower())


def get_crypto_price(ticker: str) -> dict[str, Any]:
    """
    Fetch current price and market data for a cryptocurrency.

    Uses the CoinGecko API to retrieve:
    - Current price in USD
    - 24-hour price change percentage
    - Market capitalization
    - 24-hour trading volume
    - All-time high and its date
    - Price change over 7 days and 30 days

    Args:
        ticker: The cryptocurrency ticker symbol (e.g., 'BTC', 'ETH')

    Returns:
        A dictionary containing price and market data, or an error message

    Example:
        >>> data = get_crypto_price("BTC")
        >>> print(data["current_price"])
        67234.56
    """
    coin_id = get_coingecko_id(ticker)

    try:
        # Use the /coins/{id} endpoint for comprehensive data
        url = f"{COINGECKO_API_URL}/coins/{coin_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "community_data": "false",
            "developer_data": "false",
            "sparkline": "false",
        }

        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        # Extract the relevant market data
        market_data = data.get("market_data", {})

        return {
            "success": True,
            "ticker": ticker.upper(),
            "name": data.get("name", "Unknown"),
            "symbol": data.get("symbol", ticker).upper(),
            "current_price": market_data.get("current_price", {}).get("usd"),
            "price_change_24h": market_data.get("price_change_percentage_24h"),
            "price_change_7d": market_data.get("price_change_percentage_7d"),
            "price_change_30d": market_data.get("price_change_percentage_30d"),
            "market_cap": market_data.get("market_cap", {}).get("usd"),
            "market_cap_rank": market_data.get("market_cap_rank"),
            "volume_24h": market_data.get("total_volume", {}).get("usd"),
            "high_24h": market_data.get("high_24h", {}).get("usd"),
            "low_24h": market_data.get("low_24h", {}).get("usd"),
            "ath": market_data.get("ath", {}).get("usd"),
            "ath_date": market_data.get("ath_date", {}).get("usd"),
            "circulating_supply": market_data.get("circulating_supply"),
            "total_supply": market_data.get("total_supply"),
            "last_updated": data.get("last_updated"),
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {
                "success": False,
                "error": f"Cryptocurrency '{ticker}' not found. Please check the ticker symbol.",
            }
        return {
            "success": False,
            "error": f"API error: {e.response.status_code} - {e.response.text}",
        }
    except httpx.RequestError as e:
        return {
            "success": False,
            "error": f"Network error: Unable to connect to CoinGecko API. {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
        }


def get_price_tool_definition() -> dict[str, Any]:
    """
    Get the tool definition for the price fetching tool.

    This is used by the Anthropic API to understand what the tool does
    and what parameters it accepts.

    Returns:
        A dictionary containing the tool definition in Anthropic's format
    """
    return {
        "name": "get_crypto_price",
        "description": (
            "Fetches current price and market data for a cryptocurrency from CoinGecko. "
            "Returns current price in USD, 24h/7d/30d price changes, market cap, "
            "trading volume, and other market statistics."
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
                }
            },
            "required": ["ticker"],
        },
    }
