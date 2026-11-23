"""Deterministic synthesis: fetched CMC data -> plain-language briefs.

No LLM, no predictions, no shilling. Every number comes from the API
response (or labeled mock data). Verdicts are template-based comparisons
of the numbers that were actually fetched, with the thresholds stated
in the text so the reader can see the reasoning.
"""

from __future__ import annotations

from .intents import STABLES

FOOTER = "Data summary from CoinMarketCap, not investment advice."


# -- formatting ---------------------------------------------------------
def fmt_usd(n):
    if n is None:
        return "n/a"
    n = float(n)
    if abs(n) >= 1e12:
        return f"${n / 1e12:,.2f}T"
    if abs(n) >= 1e9:
        return f"${n / 1e9:,.2f}B"
    if abs(n) >= 1e6:
        return f"${n / 1e6:,.2f}M"
    if abs(n) >= 1e3:
        return f"${n / 1e3:,.2f}K"
    return f"${n:,.2f}"


def fmt_price(p):
    if p is None:
        return "n/a"
    p = float(p)
    if p >= 1:
        return f"${p:,.2f}"
    if p >= 0.01:
        return f"${p:,.4f}"
    return f"${p:,.6f}"


def fmt_pct(x, signed=True):
    if x is None:
        return "n/a"
    sign = "+" if (signed and x > 0) else ""
    return f"{sign}{float(x):.1f}%"


def quote(coin):
    return coin.get("quote", {}).get("USD", {})


def pct(coin, field):
    return quote(coin).get(field)


def _change_word(x):
    if x is None:
        return "flat"
    if x > 0:
        return "up"
    if x < 0:
        return "down"
    return "flat"


# -- coin brief ----------------------------------------------------------
def brief_coin(coin, info=None, metrics=None):
    q = quote(coin)
    name = coin.get("name", "?")
    symbol = coin.get("symbol", "?")
    rank = coin.get("cmc_rank", "?")
    price = q.get("price")
    p24, p7, p30 = q.get("percent_change_24h"), q.get("percent_change_7d"), q.get("percent_change_30d")
    mcap = q.get("market_cap")
    vol = q.get("volume_24h")
    supply = coin.get("circulating_supply")

    lines = [f"{name} ({symbol}) — rank #{rank}"]
    lines.append(
        f"Price: {fmt_price(price)} | 24h: {fmt_pct(p24)} | 7d: {fmt_pct(p7)} | 30d: {fmt_pct(p30)}"
    )
    lines.append(f"Market cap: {fmt_usd(mcap)} | 24h volume: {fmt_usd(vol)}")
    if supply:
        lines.append(f"Circulating supply: {supply:,.0f} {symbol}")

    # Momentum: week vs month.
    if p7 is not None and p30 is not None:
        if p7 > 0 and p30 < 0:
            momentum = f"up {p7:.1f}% over 7 days after a {abs(p30):.1f}% drop over 30 days — a bounce, not a breakout."
        elif p7 > 0 and p30 > 0:
            momentum = f"up on both the week ({fmt_pct(p7)}) and the month ({fmt_pct(p30)})."
        elif p7 < 0 and p30 < 0:
            momentum = f"down on both the week ({fmt_pct(p7)}) and the month ({fmt_pct(p30)})."
        else:
            momentum = f"down {abs(p7):.1f}% this week after rising {p30:.1f}% over the month — cooling off."
    else:
        momentum = "not enough change data to judge momentum."
    # Volume health: 24h volume as a share of market cap.
    ratio = (vol / mcap * 100) if vol and mcap else None
    if ratio is None:
        volume_note = "Volume data missing."
    elif ratio > 5:
        volume_note = f"24h volume is {ratio:.1f}% of market cap — very active trading relative to size."
    elif ratio >= 1:
        volume_note = f"24h volume is {ratio:.1f}% of market cap — active trading."
    else:
        volume_note = f"24h volume is {ratio:.1f}% of market cap — quiet trading."

    if metrics:
        dom = metrics.get("btc_dominance") or metrics.get("quote", {}).get("USD", {}).get("btc_dominance")
        if symbol == "BTC" and dom is not None:
            volume_note += f" BTC is {dom:.1f}% of the whole market."

    if info and info.get("description"):
        lines.append("")
        lines.append(info["description"][:280])
    lines.append("")
    lines.append(f"Verdict: {momentum} {volume_note}")
    lines.append(FOOTER)
    return "\n".join(lines)


# -- gainers -------------------------------------------------------------
def gainers_brief(rows, days, min_volume_usd=1_000_000, limit=10):
    field = {1: "percent_change_24h", 7: "percent_change_7d", 30: "percent_change_30d"}.get(days, "percent_change_7d")
    label = {1: "24h", 7: "7d", 30: "30d"}.get(days, "7d")
    movers = []
    for c in rows:
        if c["symbol"] in STABLES:
            continue
        q = quote(c)
        if (q.get("volume_24h") or 0) < min_volume_usd:
            continue
        change = q.get(field)
        if change is None:
            continue
        movers.append((c, change))
    movers.sort(key=lambda t: t[1], reverse=True)
    movers = movers[:limit]

    lines = [f"Top gainers — {label}, min 24h volume {fmt_usd(min_volume_usd)} ({len(movers)} shown)"]
    lines.append(f"{'#':>2}  {'Symbol':<7} {'Price':>12}  {label + ' change':>9}  {'24h volume':>12}")
    for i, (c, change) in enumerate(movers, 1):
        q = quote(c)
        lines.append(
            f"{i:>2}  {c['symbol']:<7} {fmt_price(q.get('price')):>12}  {fmt_pct(change):>9}  {fmt_usd(q.get('volume_24h')):>12}"
        )
    if not movers:
        lines.append("No coins cleared the volume filter.")
        lines.append(FOOTER)
        return "\n".join(lines)

    leader, lead_change = movers[0]
    broad = sum(1 for _, ch in movers if ch > 5)
    min_vol = min(quote(c).get("volume_24h") or 0 for c, _ in movers)
    lines.append("")
    lines.append(
        f"Verdict: {leader['symbol']} leads the {label} at {fmt_pct(lead_change)}. "
        f"Gains are {'broad' if broad >= len(movers) / 2 else 'concentrated'}: "
        f"{broad} of the top {len(movers)} are up more than 5% over {label}. "
        f"The thinnest leader still did {fmt_usd(min_vol)} of 24h volume, so none of these look like empty pumps."
    )
    lines.append(FOOTER)
    return "\n".join(lines)


# -- flows ---------------------------------------------------------------
def estimated_flow(mcap, pct_change):
    """Estimated flow from a market-cap change: mcap * p / (1 + p).

    An estimate, not a measured exchange inflow — labeled as such everywhere.
    """
    if mcap is None or pct_change is None:
        return None
    p = pct_change / 100.0
    return mcap * p / (1 + p)


def flows_brief(rows, days=7, limit=10):
    field = {1: "percent_change_24h", 7: "percent_change_7d", 30: "percent_change_30d"}.get(days, "percent_change_7d")
    label = {1: "24h", 7: "7d", 30: "30d"}.get(days, "7d")
    flows = []
    for c in rows:
        if c["symbol"] in STABLES:
            continue
        q = quote(c)
        flow = estimated_flow(q.get("market_cap"), q.get(field))
        if flow is None:
            continue
        flows.append((c, flow, q.get(field)))
    flows.sort(key=lambda t: t[1], reverse=True)
    flows = flows[:limit]

    lines = [f"Top {label} flows — estimated from market-cap change, top 20 coins by market cap"]
    lines.append(f"{'#':>2}  {'Symbol':<7} {'Est. flow':>12}  {label + ' change':>9}")
    for i, (c, flow, change) in enumerate(flows, 1):
        lines.append(f"{i:>2}  {c['symbol']:<7} {fmt_usd(flow):>12}  {fmt_pct(change):>9}")
    lines.append("")
    lines.append(
        "Note: these are estimates (market cap x change), not measured exchange inflows. "
        "A positive number means the coin's market value grew over the window."
    )
    if flows:
        top, top_flow, top_change = flows[0]
        gainers = sum(1 for _, f, _ in flows if f > 0)
        lines.append(
            f"Verdict: {top['symbol']} pulled in the most over {label} at about {fmt_usd(top_flow)} "
            f"({fmt_pct(top_change)}). {gainers} of the top {len(flows)} coins by market cap gained value "
            f"over the window — money is {'spreading' if gainers >= len(flows) / 2 else 'concentrated'}."
        )
    lines.append(FOOTER)
    return "\n".join(lines)


# -- market overview -------------------------------------------------------
def market_brief(g):
    q = g.get("quote", {}).get("USD", {})
    total = q.get("total_market_cap")
    total_chg = q.get("total_market_cap_yesterday_percentage_change")
    vol = q.get("total_volume_24h")
    btc_dom = g.get("btc_dominance") or q.get("btc_dominance")
    eth_dom = g.get("eth_dominance") or q.get("eth_dominance")

    lines = ["Market overview"]
    lines.append(
        f"Total market cap: {fmt_usd(total)} (24h: {fmt_pct(total_chg)}) | 24h volume: {fmt_usd(vol)}"
    )
    lines.append(f"BTC dominance: {fmt_pct(btc_dom, signed=False)} | ETH dominance: {fmt_pct(eth_dom, signed=False)}")
    lines.append(
        f"Active: {g.get('active_cryptocurrencies', 'n/a'):,} cryptocurrencies · "
        f"{g.get('active_exchanges', 'n/a'):,} exchanges · "
        f"{g.get('active_market_pairs', 'n/a'):,} market pairs"
    )
    lines.append("")
    if btc_dom is not None:
        if btc_dom > 55:
            dom_note = f"Bitcoin holds {btc_dom:.1f}% of the market — money is concentrated in BTC, not rotating into alts."
        elif btc_dom >= 45:
            dom_note = f"Bitcoin holds {btc_dom:.1f}% of the market — a balanced split between BTC and alts."
        else:
            dom_note = f"Bitcoin holds only {btc_dom:.1f}% of the market — money is rotating into alts."
    else:
        dom_note = "Dominance data missing."
    if total_chg is not None:
        market_line = f"The total market is {_change_word(total_chg)} {abs(total_chg):.1f}% in 24 hours. {dom_note}"
    else:
        market_line = f"Total 24h change unavailable. {dom_note}"
    lines.append(f"Verdict: {market_line}")
    lines.append(FOOTER)
    return "\n".join(lines)


def top_brief(rows, limit=10):
    lines = [f"Top {limit} by market cap"]
    lines.append(f"{'#':>2}  {'Symbol':<7} {'Price':>12}  {'24h':>7}  {'7d':>7}  {'Market cap':>12}")
    for c in rows[:limit]:
        q = quote(c)
        lines.append(
            f"{c.get('cmc_rank', '?'):>2}  {c['symbol']:<7} {fmt_price(q.get('price')):>12}  "
            f"{fmt_pct(q.get('percent_change_24h')):>7}  {fmt_pct(q.get('percent_change_7d')):>7}  "
            f"{fmt_usd(q.get('market_cap')):>12}"
        )
    lines.append(FOOTER)
    return "\n".join(lines)


# -- overheated check ------------------------------------------------------
def overheated_brief(coin, metrics=None):
    q = quote(coin)
    symbol = coin.get("symbol", "?")
    name = coin.get("name", symbol)
    p7 = q.get("percent_change_7d")
    p30 = q.get("percent_change_30d")
    p90 = q.get("percent_change_90d")

    lines = [f"{name} ({symbol}) — overheated check"]
    lines.append(f"7d: {fmt_pct(p7)} | 30d: {fmt_pct(p30)} | 90d: {fmt_pct(p90)}")
    lines.append("")

    # Thresholds are stated in the verdict so the reading is transparent.
    if p7 is not None and p30 is not None:
        if p7 > 15 or p30 > 50:
            verdict = (
                f"Running hot. {symbol} is {fmt_pct(p7)} in 7 days and {fmt_pct(p30)} in 30 days — "
                "that clears the hot thresholds (7d above 15% or 30d above 50%). "
                "Fast moves like this have historically been followed by sharp pullbacks, "
                "but this check describes the move, it does not predict the next one."
            )
        elif p7 > 8 or p30 > 25:
            verdict = (
                f"Warming up. {symbol} is {fmt_pct(p7)} in 7 days and {fmt_pct(p30)} in 30 days — "
                "above average, below the hot thresholds (7d above 15% or 30d above 50%)."
            )
        elif p7 < -10:
            verdict = (
                f"Cooling off. {symbol} is down {abs(p7):.1f}% in 7 days — a pullback, "
                "not a blow-off top."
            )
        else:
            verdict = (
                f"Not overheated. {symbol} is {fmt_pct(p7)} over 7 days and {fmt_pct(p30)} over 30 days — "
                "no extreme move. A hot reading needs a 7d gain above 15% or a 30d gain above 50%."
            )
    else:
        verdict = "Not enough change data to judge."
    lines.append(f"Verdict: {verdict}")
    lines.append(FOOTER)
    return "\n".join(lines)
