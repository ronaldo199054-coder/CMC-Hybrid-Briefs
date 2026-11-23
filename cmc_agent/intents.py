"""Plain-language question -> intent parsing (keyword rules, no LLM).

Intents: gainers, flows, overheated, market, top, brief, overview.
"""

from __future__ import annotations

import re

KNOWN_COINS = {
    "btc": "BTC", "bitcoin": "BTC",
    "eth": "ETH", "ethereum": "ETH",
    "sol": "SOL", "solana": "SOL",
    "xrp": "XRP", "ripple": "XRP",
    "bnb": "BNB", "binance coin": "BNB", "binancecoin": "BNB",
    "doge": "DOGE", "dogecoin": "DOGE",
    "ada": "ADA", "cardano": "ADA",
    "link": "LINK", "chainlink": "LINK",
    "ltc": "LTC", "litecoin": "LTC",
    "avax": "AVAX", "avalanche": "AVAX",
    "trx": "TRX", "tron": "TRX",
    "ton": "TON", "toncoin": "TON",
    "dot": "DOT", "polkadot": "DOT",
    "near": "NEAR",
    "uni": "UNI", "uniswap": "UNI",
    "atom": "ATOM", "cosmos": "ATOM",
}

# Stablecoins / wrapped assets: excluded from gainers and flows.
STABLES = {"USDT", "USDC", "DAI", "FDUSD", "USDE", "TUSD", "PYUSD", "STETH", "WBTC"}


def detect_days(text):
    """Return the lookback window in days implied by the question."""
    if re.search(r"\b30d\b|30-day|30 day|month", text):
        return 30
    if re.search(r"\b7d\b|7-day|7 day|week", text):
        return 7
    if re.search(r"\b24h\b|24-hour|24 hour|today|past day", text):
        return 1
    return 7  # default window


def detect_symbol(text):
    """Return a coin symbol mentioned in the text, or None."""
    lowered = text.lower()
    # Multi-word names first ("binance coin").
    for name, symbol in sorted(KNOWN_COINS.items(), key=lambda kv: -len(kv[0])):
        if " " in name and name in lowered:
            return symbol
    tokens = re.findall(r"[a-z0-9]+", lowered)
    for token in tokens:
        if token in KNOWN_COINS:
            return KNOWN_COINS[token]
    return None


def parse_question(question):
    """Parse a plain-language question into (intent, params)."""
    text = (question or "").lower().strip()
    days = detect_days(text)
    symbol = detect_symbol(text)

    if any(w in text for w in ("gainer", "biggest gain", "top gain", "pump", "moon")):
        return "gainers", {"days": days, "limit": 10}
    if "inflow" in text or "flows" in text or "flowing" in text or "money in" in text:
        return "flows", {"days": days, "limit": 10}
    if any(w in text for w in ("overheat", "overheated", "too hot", "overbought", "bubble", "correction")):
        return "overheated", {"symbol": symbol or "BTC"}
    if "market" in text or "dominance" in text or "overall" in text or "whole market" in text:
        return "market", {}
    m = re.search(r"top\s*(\d+)", text)
    if m:
        return "top", {"limit": max(1, min(int(m.group(1)), 50))}
    if symbol:
        return "brief", {"symbol": symbol}
    if "brief" in text or "summary" in text:
        return "market", {}
    return "overview", {}
