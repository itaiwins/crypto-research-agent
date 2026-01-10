"""
Entry point for running the package as a module.

Usage:
    python -m src research BTC
    python -m src price ETH
"""

from .cli import main

if __name__ == "__main__":
    main()
