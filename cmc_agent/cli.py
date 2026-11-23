"""Command-line interface for the CMC research agent.

Usage:
    python -m cmc_agent ask "which top-20 coins had the biggest 7d inflows"
    python -m cmc_agent brief btc
    python -m cmc_agent gainers
    python -m cmc_agent flows
    python -m cmc_agent market
    python -m cmc_agent status
    python -m cmc_agent record BTC --query "brief BTC"
    python -m cmc_agent record BTC --query "brief BTC" --contract 0x... --check 0x...

Add --mock anywhere to force labeled mock data (also the automatic
fallback when no CMC_API_KEY is set). Add --json to dump the raw API
responses after the brief.

`record` is offline by default: it hashes the query and prints the
unsigned recordQuery transaction for the user to sign in their own
wallet. It never holds a private key and never broadcasts anything.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__, brief as brief_mod
from .client import CMCError, CMCClient, load_dotenv
from .hybrid import build_grounded_prompt, route_feature
from .intents import detect_symbol, parse_question
from .record import (
    DEFAULT_RPC,
    RecordError,
    check_holds_agent_id,
    encode_record_calldata,
    query_hash,
    validate_address,
    validate_symbol,
)

MOCK_BANNER = "[mock] No CMC_API_KEY set — showing labeled mock data (not real market data)."


def _hint_for_error(exc):
    code = getattr(exc, "code", None)
    if code in (401, 1001):
        return "Check that CMC_API_KEY is a valid CoinMarketCap Pro API key."
    if code == 1006:
        return "Your plan does not include this endpoint. This agent only uses Basic-plan endpoints."
    if code in (429, 1008, 1009, 1010, 1011):
        return "Rate limit hit — wait a minute and retry."
    if code in (400, 1002):
        return "Bad request — check the symbol or parameters."
    return "Run with --mock to see the same brief with labeled mock data."


def _build_client(args):
    load_dotenv()
    client = CMCClient(mock=getattr(args, "mock", False))
    return client


def _print_output(client, text, args):
    if client.mock:
        if client.api_key:
            print("[mock] --mock given — showing labeled mock data (not real market data).")
        else:
            print(MOCK_BANNER)
        print()
    print(text)
    print()
    for line in client.evidence_lines():
        print(line)
    if getattr(args, "json", False):
        print()
        print("--- raw API responses ---")
        print(json.dumps(client.raw, indent=2))


def cmd_ask(client, args):
    intent, params = parse_question(args.question)
    if intent == "gainers":
        rows = client.listings_latest(limit=100)
        _print_output(client, brief_mod.gainers_brief(rows, params["days"], limit=params["limit"]), args)
    elif intent == "flows":
        rows = client.listings_latest(limit=20)
        _print_output(client, brief_mod.flows_brief(rows, params["days"], params["limit"]), args)
    elif intent == "overheated":
        coin = client.quotes_latest(params["symbol"])
        _print_output(client, brief_mod.overheated_brief(coin), args)
    elif intent == "market":
        g = client.global_metrics()
        _print_output(client, brief_mod.market_brief(g), args)
    elif intent == "top":
        rows = client.listings_latest(limit=params["limit"])
        _print_output(client, brief_mod.top_brief(rows, params["limit"]), args)
    elif intent == "brief":
        coin = client.quotes_latest(params["symbol"])
        info = client.coin_info(params["symbol"])
        metrics = client.global_metrics()
        _print_output(client, brief_mod.brief_coin(coin, info, metrics), args)
    else:  # overview
        g = client.global_metrics()
        rows = client.listings_latest(limit=100)
        overview = brief_mod.market_brief(g)
        overview += "\n\n" + brief_mod.gainers_brief(rows, 7)
        _print_output(client, overview, args)
    return 0


def cmd_brief(client, args):
    symbol = detect_symbol(args.symbol) or args.symbol.upper()
    coin = client.quotes_latest(symbol)
    info = client.coin_info(symbol)
    metrics = client.global_metrics()
    _print_output(client, brief_mod.brief_coin(coin, info, metrics), args)
    return 0


def cmd_gainers(client, args):
    rows = client.listings_latest(limit=100)
    _print_output(client, brief_mod.gainers_brief(rows, args.days, limit=args.limit), args)
    return 0


def cmd_flows(client, args):
    rows = client.listings_latest(limit=20)
    _print_output(client, brief_mod.flows_brief(rows, args.days, args.limit), args)
    return 0


def cmd_market(client, args):
    g = client.global_metrics()
    rows = client.listings_latest(limit=10)
    text = brief_mod.market_brief(g)
    text += "\n\n" + brief_mod.top_brief(rows, 3)
    _print_output(client, text, args)
    return 0


def cmd_status(client, args):
    info = client.key_info()
    plan = info.get("plan", {})
    usage = info.get("usage", {})
    month = usage.get("current_month", {})
    limit = plan.get("credit_limit_monthly")
    used = month.get("credits_used")
    if isinstance(limit, int):
        plan_line = f"Plan: {plan.get('name', 'n/a')} | monthly credit limit: {limit:,}"
    else:
        plan_line = f"Plan: {plan.get('name', 'n/a')}"
    lines = [
        "CMC API key status",
        plan_line,
        f"Credits used this month: {used if isinstance(used, int) else 'n/a'}",
    ]
    if isinstance(limit, int) and isinstance(used, int):
        lines.append(f"Credits remaining this month: {limit - used:,}")
    lines.append(f"Rate limit: {plan.get('rate_limit_minute', 'n/a')} requests/minute")
    _print_output(client, "\n".join(lines), args)
    return 0


def cmd_hybrid(client, args):
    """Show the hybrid routing decision + grounded prompt for a coin.

    No model is called here: AI inference runs only in the web app
    (web/app.js) through Firebase AI Logic. This command exists so the
    routing and the exact prompt can be inspected and tested without a
    Firebase project or a browser.
    """
    symbol = detect_symbol(args.symbol) or args.symbol.upper()
    coin = client.quotes_latest(symbol)
    info = client.coin_info(symbol)
    metrics = client.global_metrics()
    brief_text = brief_mod.brief_coin(coin, info, metrics)
    try:
        mode = route_feature(args.feature, private=args.private, online=True)
    except (ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    prompt = build_grounded_prompt(brief_text, question=f"brief {symbol}")
    print(f"Feature: {args.feature} | Firebase AI Logic mode: {mode}")
    print("Inference runs in the web app only (web/app.js, Firebase AI Logic).")
    print()
    print("--- deterministic brief (live CMC data) ---")
    print(brief_text)
    print()
    print("--- grounded prompt sent to the model ---")
    print(prompt)
    print()
    for line in client.evidence_lines():
        print(line)
    return 0


def cmd_record(args):
    """Build (but do not send) a recordQuery transaction.

    Prints the keccak256 query hash, the ABI-encoded call data and an
    unsigned tx template for the user's own wallet. With --check, first
    does a read-only holdsAgentId call so a non-holder does not waste gas.
    Returns 0 on success, 1 on bad input, 2 when the --check fails.
    """
    try:
        symbol = validate_symbol(args.symbol)
        query = args.query or f"CMC brief {symbol}"
        qhash = query_hash(query)
        calldata = encode_record_calldata(qhash, symbol)
        contract = validate_address(args.contract, "contract address") if args.contract else None
    except RecordError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.check:
        if not contract:
            print("Error: --check needs --contract <deployed address> (contract not deployed yet).",
                  file=sys.stderr)
            return 1
        try:
            holds = check_holds_agent_id(args.rpc, contract, args.check)
        except RecordError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2
        print(f"Agent ID check: {args.check} holds an Agent ID: {holds}")
        if not holds:
            print("Do not submit — recordQuery would revert (CMCQueryReceipt: no Agent ID).")
            return 2
        print()

    print("CMC query receipt — unsigned transaction (sign in your own wallet)")
    print(f"Query: {query}")
    print(f"Symbol: {symbol}")
    print(f"queryHash (keccak256): 0x{qhash.hex()}")
    print(f"Call data: 0x{calldata.hex()}")
    print()
    print("Unsigned tx template:")
    print(f"  to:    {contract if contract else '(not deployed yet — deploy first, then re-run with --contract <address>)'}")
    print("  value: 0")
    print(f"  data:  0x{calldata.hex()}")
    if not contract:
        print()
        print("Note: the receipt contract is not deployed yet, so there is no")
        print("address to send to. Deploy contracts/CMCQueryReceipt.sol on BSC")
        print("testnet first (free test BNB), then mainnet, and re-run with")
        print("--contract <deployed address>. Only the mainnet address counts")
        print("for the Agent ID Hackathon submission (closes 2026-12-09 16:00 Beijing).")
    return 0


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    # SUPPRESS so the subparser default does not overwrite a flag given
    # before the subcommand (argparse subparsers reset shared defaults).
    common.add_argument("--mock", action="store_true", default=argparse.SUPPRESS,
                        help="use labeled mock data, no live calls")
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS,
                        help="dump raw API responses after the brief")

    parser = argparse.ArgumentParser(
        prog="cmc_agent",
        parents=[common],
        description="CMC research agent — plain-language crypto briefs from live CoinMarketCap data.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ask", parents=[common], help="ask a plain-language question")
    p.add_argument("question", help='e.g. "which top-20 coins had the biggest 7d inflows"')
    p.set_defaults(func=cmd_ask)

    p = sub.add_parser("brief", parents=[common], help="brief on one coin")
    p.add_argument("symbol", help="coin symbol, e.g. btc")
    p.set_defaults(func=cmd_brief)

    p = sub.add_parser("gainers", parents=[common], help="top gainers with real volume")
    p.add_argument("--days", type=int, choices=[1, 7, 30], default=7, help="lookback window (default 7)")
    p.add_argument("--limit", type=int, default=10, help="how many to show (default 10)")
    p.set_defaults(func=cmd_gainers)

    p = sub.add_parser("flows", parents=[common], help="top estimated flows among top-20 coins")
    p.add_argument("--days", type=int, choices=[1, 7, 30], default=7, help="lookback window (default 7)")
    p.add_argument("--limit", type=int, default=10, help="how many to show (default 10)")
    p.set_defaults(func=cmd_flows)

    p = sub.add_parser("market", parents=[common], help="market overview: total cap, dominance, top movers")
    p.set_defaults(func=cmd_market)

    p = sub.add_parser("status", parents=[common], help="show plan and credit usage for the API key")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("hybrid", parents=[common],
                        help="show hybrid routing + grounded prompt (no model call; inference runs in the web app)")
    p.add_argument("symbol", help="coin symbol, e.g. btc")
    p.add_argument("--feature", choices=["quick_verdict", "deep_brief"],
                   default="quick_verdict",
                   help="quick_verdict = prefer on-device, deep_brief = prefer cloud (default quick_verdict)")
    p.add_argument("--private", action="store_true",
                   help="keep on-device only (ONLY_ON_DEVICE, never falls back to cloud)")
    p.set_defaults(func=cmd_hybrid)

    p = sub.add_parser("record", help="build an unsigned Agent ID receipt tx (you sign it yourself)")
    p.add_argument("symbol", help="coin symbol, e.g. BTC")
    p.add_argument("--query", default=None,
                   help='query text hashed into the receipt (default: "CMC brief <SYMBOL>")')
    p.add_argument("--contract", default=None,
                   help="deployed CMCQueryReceipt address (omit until deployed)")
    p.add_argument("--rpc", default=DEFAULT_RPC,
                   help="BSC JSON-RPC URL, only used with --check")
    p.add_argument("--check", default=None, metavar="ADDRESS",
                   help="read-only: check this address holds an Agent ID before submitting")
    p.set_defaults(func=None)  # handled in main() — record needs no CMC client

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command == "record":
        # No CMC key, no CMC calls, no private key — offline by default.
        return cmd_record(args)
    client = _build_client(args)
    try:
        return args.func(client, args)
    except CMCError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        print(f"Hint: {_hint_for_error(exc)}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
