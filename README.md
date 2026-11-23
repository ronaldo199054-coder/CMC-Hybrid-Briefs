# CMC Hybrid Briefs — #BuildHybridAI 2026

A generative AI web app that answers plain-language crypto questions with
live CoinMarketCap data — and writes the verdict with AI that runs
**on-device when it can, in the cloud when it must**, all through
**Firebase AI Logic**.

Built for **#BuildHybridAI 2026** (Devpost, Google / Firebase).
Platform: **Web (Chrome)** — Gemini Nano 4 on-device, Gemini in the cloud.

> Deadline verified against the official FAQ
> (https://firebasehybridaihackathon.devpost.com/details/faqs, checked
> 2026-11-23): submissions close **Monday, Nov 30, 2026, 2:00 PM PT =
> Dec 1, 2026, 06:00 Beijing**. Total prizes **$30,000** (Grand Prize
> **$10,000**, 1st Runner-Up $7,000, 2nd Runner-Up $4,000, $3,000 each
> for Best iOS / Best Android / Best Web-Chrome). Mainland China is
> **not** in the excluded-residence list.

## The idea

Crypto "AI" answers usually do one of two bad things: they invent numbers,
or they send everything — including your question — to a server. This app
does neither:

1. **Numbers come from data, never from the model.** A deterministic brief
   is built from live CoinMarketCap API responses (price, changes, market
   cap, volume, dominance). The model only receives that brief, verbatim,
   and is instructed to use *only* its numbers.
2. **The verdict runs where it should.** A quick verdict runs
   **on-device** (Gemini Nano 4 via Firebase AI Logic `PREFER_ON_DEVICE`):
   fast, private, works offline. A deep brief runs **in the cloud**
   (Gemini 2.5 Flash via `PREFER_IN_CLOUD`). A "keep on-device" toggle
   forces `ONLY_ON_DEVICE` — the question never leaves the device.
3. **The app shows where the answer ran.** Every verdict carries an
   `ON_DEVICE` / `IN_CLOUD` badge (from `response.inferenceSource`) and
   a grounding check that flags any number not present in the brief.

## What changed vs the CMC base

Base: `cmc-agent` (Python CLI: `ask`, `brief`, `gainers`, `flows`,
`market`, `status`, `record`; deterministic template synthesis, **no
LLM**). The base is the submitted entry for CMC Round 2 and the Binance
Agent ID Hackathon — its `main` branch was not touched; this folder is a
separate copy, adapted only here.

| Area | Base | This adaptation |
|---|---|---|
| Interface | Terminal CLI only | **+ Web app** (`web/`) — the eligible platform (Web / Chrome) |
| AI | None (template text) | **Firebase AI Logic, hybrid inference** (`web/app.js`): `getGenerativeModel` + `InferenceMode` (`PREFER_ON_DEVICE` / `PREFER_IN_CLOUD` / `ONLY_ON_DEVICE`), `response.inferenceSource` badge |
| Routing policy | — | **New `cmc_agent/hybrid.py`**: per-feature mode decision + grounded-prompt builder + grounding guard; single source of truth, unit-tested |
| Data bridge | CLI calls CMC directly | **New `cmc_agent/server.py`**: stdlib-only local server — serves `web/` and `/api/*` (brief, market, gainers, ask, hybrid-preview, status). Data only; it calls **no** model API |
| CLI | `ask/brief/gainers/flows/market/status/record` | **+ `hybrid <symbol>`**: prints the routing decision + the exact grounded prompt (no model call — inspection/testing only) |
| Secrets | `.env` with `CMC_API_KEY` | Same, but **this folder has its own `.env`** (mode 600). Firebase config lives in `web/firebase-config.js` (git-ignored, example provided). App Check debug tokens are never committed |
| Unchanged | `client.py`, `brief.py`, `intents.py`, `record.py`, `contracts/`, tests | Reused as-is (except version bump to 0.2.0) |

## Architecture

```
Chrome (desktop)                Local server (this repo)        External services
┌──────────────────────┐        ┌─────────────────────┐        ┌──────────────────┐
│ web/index.html       │        │ python -m           │        │ CoinMarketCap    │
│ web/app.js           │───────▶│ cmc_agent.server    │───────▶│ Pro API (data    │
│  ├─ Firebase AI     │ /api/* │  ├─ CMCClient       │        │ only, 5 Basic-   │
│  │   Logic:          │        │  ├─ brief.py        │        │ plan endpoints)  │
│  │   PREFER_ON_DEVICE│        │  └─ hybrid.py       │        └──────────────────┘
│  │   (Gemini Nano 4) │        │     (routing+prompt) │        ┌──────────────────┐
│  │   PREFER_IN_CLOUD │        └─────────────────────┘        │ Firebase AI      │
│  │   (Gemini cloud)  │                ▲                      │ Logic (all AI    │
│  └─ App Check        │                │ prompt only           │ inference)       │
└──────────────────────┘                └────────────────────── └──────────────────┘
```

All AI inference goes through Firebase AI Logic. The Python side never
calls any model API; the server only returns data and the prompt text.

## Quick start

Requires Python 3.10+ and Chrome (desktop, v139+) for on-device inference.

```bash
pip install -r requirements.txt

# 1. CoinMarketCap key — this folder's OWN .env, mode 600.
#    Get a free key at https://pro.coinmarketcap.com/signup/
cp .env.example .env
chmod 600 .env
# edit .env and paste your key (never commit it)

# 2. Firebase (for the AI verdict; data + routing preview work without it)
cp web/firebase-config.example.js web/firebase-config.js
# edit web/firebase-config.js with your Firebase project values

# 3. Chrome: enable the on-device model flag
#    chrome://flags/#prompt-api-for-gemini-nano-multimodal-input -> Enabled

# 4. Run
python -m cmc_agent.server            # live data (needs the key in .env)
python -m cmc_agent.server --mock     # labeled mock data, no key needed
# Open http://localhost:8765 in Chrome
```

Without `firebase-config.js`, the app still shows live briefs, the routing
decision and the exact prompt — and says plainly that the AI verdict needs
Firebase. It never fakes an answer.

### CLI (data + routing inspection, no model call)

```bash
python -m cmc_agent ask "is BTC overheated right now"
python -m cmc_agent hybrid btc --feature quick_verdict
python -m cmc_agent hybrid btc --feature deep_brief --private
python -m cmc_agent market
python -m cmc_agent status
```

## Firebase setup (what you must do in the console)

1. Create a Firebase project, go to **Firebase AI Logic -> Get started**,
   choose the Gemini Developer API backend.
2. **App Check is required** for Firebase AI Logic. For local development,
   set `appCheckDebugToken: true` in `web/firebase-config.js` and register
   the debug token printed in the console (Firebase console -> App Check).
   For any public deployment, use reCAPTCHA v3 (`recaptchaSiteKey`) instead
   and remove the debug token. Never commit a debug token.
3. Cloud model: the deep brief uses `gemini-3.5-flash-lite` (set in
   `web/firebase-config.js` as `cloudModel`). It is Google's designated
   replacement for the deprecated `gemini-2.5-flash` (auto-routed from
   Dec 1, 2026) and a current Firebase AI Logic model. On the Gemini
   Developer API backend it is a stable text model on the free tier, so
   no billing account and no Sprint 3 quota request are needed; billing
   would only be required if you switched to the Agent Platform
   (Vertex AI) backend. Sprint 3 (final) requests close Wed Nov 25,
   10:00 AM PT = Nov 26, 02:00 Beijing (quota form:
   https://forms.gle/uPcDhaYW3iVo2AYw5 — register for the hackathon
   first) — not needed for this entry as configured.

## Hybrid inference — how each feature runs

| Feature | Firebase AI Logic mode | Where it runs |
|---|---|---|
| Quick verdict (short, single-turn) | `PREFER_ON_DEVICE` | Gemini Nano 4 on Chrome when available; cloud fallback |
| Deep brief (longer explanation) | `PREFER_IN_CLOUD` | Cloud Gemini model (`gemini-3.5-flash-lite`) |
| Any question, "keep on-device" on | `ONLY_ON_DEVICE` | On-device only; throws instead of falling back |
| Offline | quick verdict `ONLY_ON_DEVICE`; deep brief unavailable (the app says so, it does not guess) | On-device |

On-device inference is single-turn text generation only (no chat) — the
app sends one `generateContent()` call per question, which fits that
limit. `getGenerativeModel()` is created on the Ask click, as the docs
require for `inferenceMode` to apply.

## Grounding — the model cannot invent numbers

The prompt (`cmc_agent/hybrid.py:build_grounded_prompt`) pastes the
deterministic CMC brief verbatim and instructs the model to use only those
numbers, to say when a number is missing, and to end with
"Not investment advice." A heuristic guard (`check_grounding`, mirrored
in `web/app.js`) flags any `$`- or `%`-number in the verdict that does not
appear in the brief; the flag is shown next to the verdict for the user
to judge.

## Tests

```bash
python -m unittest discover -s tests -v
```

71 tests, all offline (mock data): the original CLI/record suites plus
new `tests/test_hybrid.py` (routing, prompts, grounding guard) and
`tests/test_server.py` (real HTTP server on an ephemeral port: web app
serving, Firebase AI Logic imports in `app.js`, `/api/*` endpoints).

Verified live 2026-11-23 (key read from the original repo's `.env`,
never printed or copied): `brief btc` returned live data
(BTC $60,823.56, 3 credits) and `hybrid btc` routed `PREFER_ON_DEVICE`;
the local server served live ETH data and `deep_brief` previewed
`PREFER_IN_CLOUD`.

## Demo

- `DEMO_VIDEO_SCRIPT.md` — 90-second demo script (first 30s: idea, who
  it is for, the problem, how Firebase AI Logic makes it work).
- `demo-video/buildhybridai-demo.mp4` — rendered vertical video (Remotion;
  see the script for what each scene shows). The video shows the real
  web-app UI; re-record the screen sections with your live Firebase
  project before uploading to YouTube if you want live Nano footage.
- Old terminal demo: `examples/DEMO_SCRIPT.md` (base CLI, unchanged).

## Submission — pre-existing code disclosure

This project adapts the author's own `cmc-agent` CLI (built Nov 18–19,
2026 for the Build with CMC hackathon). Everything in `web/`,
`cmc_agent/hybrid.py`, `cmc_agent/server.py`, the `hybrid` CLI command and
the tests for them was built during the #BuildHybridAI submission period
(Nov 11–30, 2026): the Firebase AI Logic integration, the hybrid routing,
the web app, and the grounding guard are all new work for this hackathon.
The reused parts (CMC data client, deterministic briefs, intent parsing,
receipt contract) are disclosed here and in the submission form.

## License

MIT — see `LICENSE`.
