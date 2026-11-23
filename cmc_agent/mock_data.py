"""MOCK DATA — clearly labeled fixture responses for offline use.

None of these numbers are real market data. They are plausible,
round-number fixtures so the CLI, tests, and demo run without an API key.
Every CLI run in mock mode prints a MOCK banner, and every evidence block
says the credits are simulated.

Shapes mirror the real CoinMarketCap Pro API v1 responses:
- listings/latest: list of coin dicts with quote.USD
- quotes/latest: dict keyed by symbol
- info (v2): dict keyed by CMC id (as a string)
- global-metrics/quotes/latest: dict with quote.USD
- key/info: plan + usage
"""

from __future__ import annotations

import math

from .client import CMCError

# (rank, id, name, symbol, price, mcap_usd, vol24h_usd, 1h%, 24h%, 7d%, 30d%, 60d%, 90d%, circulating)
_ROWS = [
    (1, 1, "Bitcoin", "BTC", 97420.0, 1_940_000_000_000, 38_200_000_000, 0.3, 1.8, 4.2, -6.5, 12.1, 28.4, 19_920_000),
    (2, 1027, "Ethereum", "ETH", 3310.0, 398_000_000_000, 21_500_000_000, 0.1, 0.9, 2.1, -9.8, 6.3, 14.2, 120_400_000),
    (3, 825, "Tether", "USDT", 1.0, 148_000_000_000, 52_000_000_000, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 148_000_000_000),
    (4, 52, "XRP", "XRP", 2.14, 128_000_000_000, 4_100_000_000, -0.4, -1.2, -3.2, 8.7, -2.1, 22.5, 59_800_000_000),
    (5, 1839, "BNB", "BNB", 905.0, 126_000_000_000, 1_900_000_000, 0.2, 0.6, 1.2, -4.3, 9.8, 31.0, 139_000_000),
    (6, 3408, "USDC", "USDC", 1.0, 74_000_000_000, 9_800_000_000, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 74_000_000_000),
    (7, 5426, "Solana", "SOL", 148.5, 79_000_000_000, 3_600_000_000, 0.5, 3.1, 8.9, -12.4, 18.6, 42.1, 532_000_000),
    (8, 8085, "Lido Staked Ether", "STETH", 3305.0, 29_000_000_000, 400_000_000, 0.1, 0.9, 2.0, -9.7, 6.1, 13.9, 8_770_000),
    (9, 1958, "TRON", "TRX", 0.31, 27_000_000_000, 1_200_000_000, 0.1, 0.4, 1.8, 2.2, 5.4, 9.8, 86_100_000_000),
    (10, 74, "Dogecoin", "DOGE", 0.168, 25_000_000_000, 2_800_000_000, 0.8, 5.2, 12.4, -14.1, 21.3, 38.7, 148_800_000_000),
    (11, 10, "Wrapped Bitcoin", "WBTC", 97380.0, 12_400_000_000, 500_000_000, 0.3, 1.8, 4.1, -6.6, 12.0, 28.1, 127_000),
    (12, 2010, "Cardano", "ADA", 0.52, 18_500_000_000, 900_000_000, -0.2, -1.8, -5.6, -11.2, -8.4, 6.2, 35_600_000_000),
    (13, 1975, "Chainlink", "LINK", 16.8, 11_400_000_000, 700_000_000, 0.4, 2.2, 6.7, -7.9, 11.5, 19.8, 678_000_000),
    (14, 5805, "Avalanche", "AVAX", 18.9, 8_000_000_000, 500_000_000, -0.3, -2.4, -7.3, -15.6, -4.2, 8.9, 423_000_000),
    (15, 2, "Litecoin", "LTC", 96.4, 7_400_000_000, 800_000_000, 0.1, 0.5, 0.8, -3.1, 2.2, 11.4, 76_800_000),
    (16, 11419, "Toncoin", "TON", 2.9, 7_300_000_000, 200_000_000, -0.1, -0.6, -2.1, -5.4, -9.8, -1.2, 2_520_000_000),
    (17, 6636, "Polkadot", "DOT", 3.1, 4_800_000_000, 300_000_000, 0.0, 0.2, 0.9, -6.8, -3.1, 4.5, 1_550_000_000),
    (18, 6535, "NEAR Protocol", "NEAR", 2.4, 3_000_000_000, 400_000_000, 0.2, 1.1, 3.4, -9.2, 7.7, 12.6, 1_250_000_000),
    (19, 7083, "Uniswap", "UNI", 9.8, 2_900_000_000, 300_000_000, 0.3, 1.4, 4.8, -8.5, 3.9, 15.2, 296_000_000),
    (20, 3794, "Cosmos", "ATOM", 4.6, 2_200_000_000, 200_000_000, -0.2, -0.9, -1.8, -7.7, -2.4, 5.1, 478_000_000),
]

MOCK_SYMBOLS = {row[3] for row in _ROWS}


def _coin_dict(row):
    (rank, cid, name, symbol, price, mcap, vol, p1h, p24h, p7d, p30d, p60d, p90d,
     supply) = row
    return {
        "id": cid,
        "name": name,
        "symbol": symbol,
        "slug": name.lower().replace(" ", "-"),
        "cmc_rank": rank,
        "circulating_supply": supply,
        "total_supply": supply,
        "max_supply": None if symbol not in ("BTC", "LTC", "ADA", "DOT", "ATOM") else supply * 1.05,
        "quote": {
            "USD": {
                "price": price,
                "volume_24h": vol,
                "volume_change_24h": round(p24h * 3.1, 1),
                "percent_change_1h": p1h,
                "percent_change_24h": p24h,
                "percent_change_7d": p7d,
                "percent_change_30d": p30d,
                "percent_change_60d": p60d,
                "percent_change_90d": p90d,
                "market_cap": mcap,
                "market_cap_dominance": round(mcap / 3_420_000_000_000 * 100, 2),
                "fully_diluted_market_cap": mcap,
                "last_updated": "2026-11-18T14:00:00.000Z",
            }
        },
    }


MOCK_LISTINGS = [_coin_dict(r) for r in _ROWS]
MOCK_BY_SYMBOL = {c["symbol"]: c for c in MOCK_LISTINGS}

MOCK_GLOBAL = {
    "quote": {
        "USD": {
            "total_market_cap": 3_420_000_000_000,
            "total_volume_24h": 96_500_000_000,
            "total_market_cap_yesterday_percentage_change": 0.9,
            "total_volume_24h_yesterday_percentage_change": 4.2,
            "btc_dominance": 56.8,
            "eth_dominance": 12.9,
            "btc_dominance_yesterday_percentage_change": 0.1,
            "eth_dominance_yesterday_percentage_change": -0.2,
            "last_updated": "2026-11-18T14:00:00.000Z",
        }
    },
    "active_cryptocurrencies": 10240,
    "total_cryptocurrencies": 58400,
    "active_market_pairs": 104300,
    "active_exchanges": 812,
    "total_exchanges": 941,
    "eth_dominance": 12.9,
    "btc_dominance": 56.8,
    "defi_volume_24h": 8_100_000_000,
    "defi_volume_24h_reported": 8_100_000_000,
    "defi_market_cap": 148_000_000_000,
    "stablecoin_volume_24h": 71_000_000_000,
    "stablecoin_volume_24h_reported": 71_000_000_000,
    "stablecoin_market_cap": 268_000_000_000,
    "derivatives_volume_24h": 412_000_000_000,
    "derivatives_volume_24h_reported": 412_000_000_000,
    "last_updated": "2026-11-18T14:00:00.000Z",
}

MOCK_KEY_INFO = {
    "plan": {
        "credit_limit_monthly": 15000,
        "credit_limit_monthly_reset": "2026-12-01",
        "credit_limit_monthly_reset_timestamp": "2026-12-01T00:00:00.000Z",
        "name": "Basic",
        "rate_limit_minute": 50,
    },
    "usage": {
        "current_minute": {"requests_made": 2, "requests_left": 48},
        "current_day": {"credits_used": 12},
        "current_month": {"credits_used": 42},
    },
}

_MOCK_INFO_TEXT = {
    "BTC": ("Bitcoin is the first decentralized cryptocurrency, created in 2009. "
            "It runs on a proof-of-work blockchain and is the largest crypto asset by market cap."),
    "ETH": ("Ethereum is a programmable blockchain and the home of smart contracts, "
            "DeFi, and NFTs. Its native asset is ether (ETH)."),
    "SOL": ("Solana is a high-throughput layer-1 blockchain built for fast, low-cost "
            "transactions and consumer apps."),
    "XRP": ("XRP is the native asset of the XRP Ledger, a payments-focused blockchain "
            "used for cross-border settlement."),
    "BNB": ("BNB is the native asset of the BNB Chain ecosystem, used for fees, "
            "staking, and token sales on Binance's chains."),
    "DOGE": ("Dogecoin started as a joke in 2013 and became the best-known memecoin, "
            "with a large and active community."),
    "ADA": ("Cardano is a proof-of-stake layer-1 blockchain built on peer-reviewed "
            "research, with ADA as its native asset."),
    "LINK": ("Chainlink is a decentralized oracle network that brings off-chain data "
            "onto blockchains; LINK pays node operators."),
    "LTC": ("Litecoin is an early Bitcoin fork designed for faster blocks and lower "
            "fees, often called the silver to Bitcoin's gold."),
    "AVAX": ("Avalanche is a layer-1 platform for subnets and custom blockchains, "
            "with AVAX as its native asset."),
}


def _info_dict(coin):
    symbol = coin["symbol"]
    return {
        "id": coin["id"],
        "name": coin["name"],
        "symbol": symbol,
        "category": "coin",
        "description": _MOCK_INFO_TEXT.get(
            symbol, f"{coin['name']} ({symbol}) is a cryptocurrency tracked by CoinMarketCap."
        ),
        "slug": coin["slug"],
        "logo": f"https://s2.coinmarketcap.com/static/img/coins/64x64/{coin['id']}.png",
        "urls": {
            "website": [f"https://{coin['slug']}.org"],
            "twitter": [],
            "technical_doc": [],
        },
        "date_added": "2013-04-28T00:00:00.000Z",
        "platform": None,
    }


def _status(credits):
    return {
        "timestamp": "2026-11-18T14:00:00.000Z",
        "error_code": 0,
        "error_message": None,
        "elapsed": 5,
        "credit_count": credits,
        "notice": None,
    }


def mock_response(path, params):
    """Return a fixture payload shaped like the real API response."""
    if path == "/cryptocurrency/listings/latest":
        limit = int(params.get("limit", 100))
        sort = params.get("sort", "market_cap")
        rows = list(MOCK_LISTINGS)
        if sort == "percent_change_7d":
            rows.sort(key=lambda c: c["quote"]["USD"]["percent_change_7d"], reverse=True)
        elif sort == "volume_24h":
            rows.sort(key=lambda c: c["quote"]["USD"]["volume_24h"], reverse=True)
        rows = rows[: max(1, limit)]
        return {"status": _status(max(1, math.ceil(limit / 200))), "data": rows}

    if path == "/cryptocurrency/quotes/latest":
        symbol = str(params.get("symbol", "")).split(",")[0].strip().upper()
        coin = MOCK_BY_SYMBOL.get(symbol)
        if coin is None:
            raise CMCError(
                f"Symbol '{symbol}' not found in mock data "
                f"(mock covers: {', '.join(sorted(MOCK_SYMBOLS))})",
                code=400,
            )
        return {"status": _status(1), "data": {symbol: coin}}

    if path == "/cryptocurrency/info":
        symbol = str(params.get("symbol", "")).split(",")[0].strip().upper()
        coin = MOCK_BY_SYMBOL.get(symbol)
        if coin is None:
            raise CMCError(
                f"Symbol '{symbol}' not found in mock data "
                f"(mock covers: {', '.join(sorted(MOCK_SYMBOLS))})",
                code=400,
            )
        return {"status": _status(1), "data": {str(coin["id"]): _info_dict(coin)}}

    if path == "/global-metrics/quotes/latest":
        return {"status": _status(1), "data": MOCK_GLOBAL}

    if path == "/key/info":
        return {"status": _status(0), "data": MOCK_KEY_INFO}

    raise CMCError(f"Mock has no fixture for {path}", code=404)
