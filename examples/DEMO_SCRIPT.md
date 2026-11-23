# Demo script — CMC research agent (60–90 seconds, terminal only)

Run this in `~/workspace/cmc-agent/` with a real key in `.env`
(or add `--mock` to any command to show the same flow with labeled mock data).

## 0:00–0:10 — The question
Say: "A research agent that answers plain-language market questions with
live CoinMarketCap data — no chat UI, just a CLI."

Type:

```bash
python -m cmc_agent ask "which top-20 coins had the biggest 7d inflows"
```

## 0:10–0:40 — The brief
Show: the brief prints concrete numbers (estimated 7d flows, 7d change per
coin) plus a two-line verdict, then the evidence block underneath:
every API call it made, endpoint + params + credits.

Point at the evidence block and say: "Every answer shows its work —
the exact endpoints, and the exact credits each call cost."

## 0:40–1:05 — A second question, a different intent
Type:

```bash
python -m cmc_agent ask "is BTC overheated right now"
```

Show: the overheated check with the 7d / 30d / 90d numbers and the verdict,
with the hot thresholds stated in the text.

## 1:05–1:20 — Market context + key status
Type:

```bash
python -m cmc_agent market
python -m cmc_agent status
```

Show: total market cap, BTC/ETH dominance, top movers — then the plan
(Basic, 15,000 credits/month) and credits used, to show the agent stays
well inside the free tier.

## 1:20–1:30 — Close
Say: "Five CoinMarketCap endpoints, all on the free Basic plan.
One to three calls per question, about one credit each. Deterministic
briefs — no LLM, no predictions, no shilling."

## Commands used (copy/paste)
```bash
python -m cmc_agent ask "which top-20 coins had the biggest 7d inflows"
python -m cmc_agent ask "is BTC overheated right now"
python -m cmc_agent market
python -m cmc_agent status
```
