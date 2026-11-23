"""CoinMarketCap Pro API client.

- Reads the API key from the CMC_API_KEY env var (or a local .env file).
- Never prints or logs the key.
- Records every call (endpoint, params, credits) so the CLI can show
  evidence of real API use.
- Mock mode: no key (or --mock) -> labeled fixture responses, no HTTP.

Endpoints used here are all available on the free Basic plan (verified
against https://coinmarketcap.com/api/documentation/v1/ and the CMC
pricing/credit reference, 2026-11-18):
- /cryptocurrency/listings/latest
- /cryptocurrency/quotes/latest
- /cryptocurrency/info
- /global-metrics/quotes/latest
- /key/info

Deliberately NOT used: the /cryptocurrency/trending/* family
(trending/latest, trending/gainers-losers, trending/most-visited) — those
require the Startup plan or above. Gainers are computed from
listings/latest instead.
"""

from __future__ import annotations

import os
from pathlib import Path

import requests

BASE_URL = "https://pro-api.coinmarketcap.com/v1"
DEFAULT_TIMEOUT = 15


class CMCError(Exception):
    """Raised for API errors (HTTP status or CMC error_code)."""

    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code


def load_dotenv(path=None):
    """Load KEY=VALUE pairs from a .env file into os.environ (no overwrite).

    Only sets variables that are not already set. Never prints values.
    Returns the .env path used, or None.
    """
    candidates = []
    if path:
        candidates.append(Path(path))
    candidates.append(Path.cwd() / ".env")
    candidates.append(Path(__file__).resolve().parent.parent / ".env")
    for candidate in candidates:
        if candidate.is_file():
            for line in candidate.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
            return candidate
    return None


class CMCClient:
    """Thin wrapper around the CoinMarketCap Pro API (v1)."""

    def __init__(self, api_key=None, mock=False, base_url=BASE_URL):
        self.api_key = api_key or os.environ.get("CMC_API_KEY") or ""
        self.mock = bool(mock) or not self.api_key
        self.base_url = base_url.rstrip("/")
        self.calls = []  # [{endpoint, params, credits, mock}]
        self.raw = []  # full response payloads, for --json output

    # -- low level -----------------------------------------------------
    def get(self, path, params=None):
        params = dict(params or {})
        if self.mock:
            from .mock_data import mock_response

            payload = mock_response(path, params)
            credits = payload.get("status", {}).get("credit_count", 0)
            self.calls.append(
                {"endpoint": path, "params": params, "credits": credits, "mock": True}
            )
            self.raw.append(payload)
            return payload["data"]
        headers = {"X-CMC_PRO_API_KEY": self.api_key, "Accept": "application/json"}
        try:
            resp = requests.get(
                f"{self.base_url}{path}", headers=headers, params=params, timeout=DEFAULT_TIMEOUT
            )
        except requests.RequestException as exc:
            raise CMCError(f"Network error calling {path}: {exc}")
        try:
            payload = resp.json()
        except ValueError:
            raise CMCError(
                f"Non-JSON response from {path} (HTTP {resp.status_code})",
                code=resp.status_code,
            )
        status = payload.get("status", {})
        if resp.status_code != 200 or status.get("error_code"):
            code = status.get("error_code", resp.status_code)
            msg = status.get("error_message") or f"HTTP {resp.status_code}"
            raise CMCError(f"{path} failed: {msg}", code=code)
        self.calls.append(
            {
                "endpoint": path,
                "params": params,
                "credits": status.get("credit_count"),
                "mock": False,
            }
        )
        self.raw.append(payload)
        return payload["data"]

    # -- endpoints (all available on the free Basic plan) ---------------
    def listings_latest(self, limit=100, sort="market_cap", convert="USD"):
        return self.get(
            "/cryptocurrency/listings/latest",
            {"start": 1, "limit": limit, "sort": sort, "convert": convert},
        )

    def quotes_latest(self, symbol, convert="USD"):
        symbol = symbol.upper()
        data = self.get(
            "/cryptocurrency/quotes/latest", {"symbol": symbol, "convert": convert}
        )
        if symbol in data:
            return data[symbol]
        if data:
            return next(iter(data.values()))
        raise CMCError(f"No data returned for symbol '{symbol}'", code=1002)

    def coin_info(self, symbol):
        symbol = symbol.upper()
        data = self.get("/cryptocurrency/info", {"symbol": symbol})
        if data:
            return next(iter(data.values()))
        raise CMCError(f"No info returned for symbol '{symbol}'", code=1002)

    def global_metrics(self, convert="USD"):
        return self.get("/global-metrics/quotes/latest", {"convert": convert})

    def key_info(self):
        return self.get("/key/info", {})

    # -- evidence ------------------------------------------------------
    def total_credits(self):
        return sum((c["credits"] or 0) for c in self.calls)

    def evidence_lines(self):
        lines = []
        mode = (
            "MOCK — no live calls made; credits shown are simulated"
            if self.mock
            else "LIVE — real API calls"
        )
        lines.append(f"API calls made ({len(self.calls)}) [{mode}]:")
        for c in self.calls:
            params = ", ".join(f"{k}={v}" for k, v in sorted(c["params"].items()))
            credits = c["credits"] if c["credits"] is not None else "?"
            lines.append(f"  - {c['endpoint']} ({params}) — {credits} credit(s)")
        lines.append(f"Total credits used: {self.total_credits()}")
        return lines
