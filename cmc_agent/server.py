"""Local demo server: serves the web app and a CMC data API.

Run from the repo root:

    python -m cmc_agent.server            # live CMC data (needs .env key)
    python -m cmc_agent.server --mock     # labeled mock data, no key
    python -m cmc_agent.server --port 8765

Then open http://localhost:8765 in Chrome.

This server is a *data* bridge only. It never calls any AI model: the
web app performs all AI inference through Firebase AI Logic in the
browser. The server exposes one extra endpoint, /api/hybrid-preview,
which returns the routing decision + grounded prompt (see hybrid.py)
so the web app can show exactly what it will send to the model.

Endpoints (all GET, JSON unless noted):
- /                     -> web/index.html
- /app.js, /styles.css -> static files from web/
- /api/brief?symbol=BTC
- /api/market
- /api/gainers?days=7&limit=10
- /api/ask?q=<plain-language question>
- /api/hybrid-preview?symbol=BTC&feature=quick_verdict|deep_brief
    [&private=1]  -> {feature, mode, cloud_model, prompt}
- /api/status           -> CMC plan / credit usage

Only stdlib is used (http.server). Binds to 127.0.0.1 by default so the
key is never exposed beyond this machine.
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import brief as brief_mod
from .client import CMCClient, CMCError, load_dotenv
from .hybrid import CLOUD_MODEL, build_grounded_prompt, route_feature
from .intents import detect_symbol, parse_question

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".svg": "image/svg+xml",
}


def make_handler(client):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # keep the demo output quiet
            pass

        def _send_json(self, payload, status=200):
            body = json.dumps(payload, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "http://localhost:8765")
            self.end_headers()
            self.wfile.write(body)

        def _send_file(self, path):
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", MIME.get(path.suffix, "application/octet-stream"))
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _brief_payload(self, text):
            return {
                "brief": text,
                "mock": client.mock,
                "evidence": client.evidence_lines(),
                "credits_used": client.total_credits(),
            }

        def _coin_brief(self, symbol):
            coin = client.quotes_latest(symbol)
            info = client.coin_info(symbol)
            metrics = client.global_metrics()
            return brief_mod.brief_coin(coin, info, metrics)

        def do_GET(self):
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            path = parsed.path
            try:
                if path == "/":
                    return self._send_file(WEB_DIR / "index.html")
                if path.startswith("/api/"):
                    return self._handle_api(path, query)
                # Static files from web/ (no directory traversal).
                target = (WEB_DIR / path.lstrip("/")).resolve()
                if str(target).startswith(str(WEB_DIR.resolve())) and target.is_file():
                    return self._send_file(target)
                return self._send_json({"error": f"not found: {path}"}, status=404)
            except CMCError as exc:
                return self._send_json({"error": str(exc)}, status=502)
            except (ValueError, RuntimeError) as exc:
                return self._send_json({"error": str(exc)}, status=400)

        def _handle_api(self, path, query):
            if path == "/api/brief":
                symbol = (query.get("symbol", ["BTC"])[0] or "BTC").upper()
                return self._send_json(self._brief_payload(self._coin_brief(symbol)))
            if path == "/api/market":
                g = client.global_metrics()
                rows = client.listings_latest(limit=10)
                text = brief_mod.market_brief(g) + "\n\n" + brief_mod.top_brief(rows, 3)
                return self._send_json(self._brief_payload(text))
            if path == "/api/gainers":
                days = int(query.get("days", ["7"])[0])
                limit = int(query.get("limit", ["10"])[0])
                rows = client.listings_latest(limit=100)
                return self._send_json(
                    self._brief_payload(brief_mod.gainers_brief(rows, days, limit=limit))
                )
            if path == "/api/ask":
                q = query.get("q", [""])[0]
                intent, params = parse_question(q)
                if intent == "gainers":
                    rows = client.listings_latest(limit=100)
                    text = brief_mod.gainers_brief(rows, params["days"], limit=params["limit"])
                elif intent == "flows":
                    rows = client.listings_latest(limit=20)
                    text = brief_mod.flows_brief(rows, params["days"], params["limit"])
                elif intent == "overheated":
                    text = brief_mod.overheated_brief(client.quotes_latest(params["symbol"]))
                elif intent == "market":
                    text = brief_mod.market_brief(client.global_metrics())
                elif intent == "top":
                    rows = client.listings_latest(limit=params["limit"])
                    text = brief_mod.top_brief(rows, params["limit"])
                elif intent == "brief":
                    text = self._coin_brief(params["symbol"])
                else:
                    g = client.global_metrics()
                    rows = client.listings_latest(limit=100)
                    text = brief_mod.market_brief(g) + "\n\n" + brief_mod.gainers_brief(rows, 7)
                payload = self._brief_payload(text)
                payload["intent"] = intent
                return self._send_json(payload)
            if path == "/api/hybrid-preview":
                symbol = (query.get("symbol", ["BTC"])[0] or "BTC").upper()
                feature = query.get("feature", ["quick_verdict"])[0]
                private = query.get("private", ["0"])[0] == "1"
                mode = route_feature(feature, private=private, online=True)
                text = self._coin_brief(symbol)
                return self._send_json(
                    {
                        "feature": feature,
                        "mode": mode,
                        "cloud_model": CLOUD_MODEL,
                        "prompt": build_grounded_prompt(text),
                        "mock": client.mock,
                    }
                )
            if path == "/api/status":
                info = client.key_info()
                return self._send_json({"plan": info.get("plan", {}), "usage": info.get("usage", {}), "mock": client.mock})
            return self._send_json({"error": f"unknown API path: {path}"}, status=404)

    return Handler


def main(argv=None):
    parser = argparse.ArgumentParser(prog="cmc_agent.server", description="Local demo server for the hybrid web app.")
    parser.add_argument("--mock", action="store_true", help="use labeled mock data, no live calls")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args(argv)
    load_dotenv()
    client = CMCClient(mock=args.mock)
    if client.mock:
        print("[mock] No CMC_API_KEY set or --mock given — serving labeled mock data.")
    server = ThreadingHTTPServer((args.host, args.port), make_handler(client))
    print(f"Serving the hybrid web app at http://{args.host}:{args.port} (Ctrl+C to stop)")
    print("Open that URL in Chrome. All AI inference runs in the browser via Firebase AI Logic.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
