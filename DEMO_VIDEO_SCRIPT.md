# Demo video script — CMC Hybrid Briefs (90 seconds, vertical 1080×1920)

Hackathon rule: up to 3 minutes on YouTube, in English, showing the project
working on the platform built for (Web / Chrome). First 30 seconds: the
idea, who it is for, the problem, and how Firebase AI Logic makes it work.
Rendered version: `demo-video/buildhybridai-demo.mp4` (Remotion, 9 scenes
× 10 s, no voiceover — on-screen text carries the narration; add voiceover
from the lines below if you re-render with audio).

Total: ~90 seconds. Narration is written at ~9 seconds per 10-second
scene, with at least 4 lines of on-screen text per scene.

## Scene 1 — 0:00–0:10 — The problem

On-screen:
- CRYPTO ANSWERS YOU CAN'T TRUST
- AI chatbots invent prices
- "Analysts" hide their sources
- Your question goes to a server, always

Say: "Crypto AI has two problems. It invents numbers. And it sends your
question to a server every single time. This app fixes both."

## Scene 2 — 0:10–0:20 — The idea

On-screen:
- CMC HYBRID BRIEFS
- Plain-English answers
- Live CoinMarketCap data
- Numbers from data — never from the model

Say: "CMC Hybrid Briefs answers plain-language crypto questions with live
CoinMarketCap data. The numbers come from the data. Never from the model."

## Scene 3 — 0:20–0:30 — How Firebase AI Logic makes it work

On-screen:
- FIREBASE AI LOGIC · HYBRID INFERENCE
- Quick verdict → on-device, Gemini Nano 4
- Deep brief → cloud, Gemini
- One SDK decides where each answer runs

Say: "It is built with Firebase AI Logic. A quick verdict runs on-device
on Gemini Nano 4. A deep brief runs in the cloud on Gemini. One SDK
decides where each answer runs."

## Scene 4 — 0:30–0:40 — It working: ask the question

On-screen (screen recording of the web app):
- Ask: "is BTC overheated right now"
- Live brief: price, 7d / 30d change, volume
- Evidence: every API call + credits
- 3 calls · 3 credits · free Basic plan

Say: "Ask in plain English. The app fetches live data and shows its work —
every API call it made, and the credits each one cost."

## Scene 5 — 0:40–0:50 — It working: the on-device verdict

On-screen (screen recording of the web app):
- Quick verdict — Firebase AI Logic
- Badge: RAN ON-DEVICE
- No server round-trip for this answer
- Same numbers as the brief — nothing invented

Say: "The quick verdict runs on-device. See the badge: ran on-device. No
server round-trip — and every number in it is in the brief."

## Scene 6 — 0:50–1:00 — It working: the cloud deep brief

On-screen (screen recording of the web app):
- Deep brief — Firebase AI Logic
- Badge: RAN IN CLOUD
- Longer explanation, same grounded numbers
- Grounding check: every number verified

Say: "Need more depth? The deep brief runs in the cloud instead. Same
grounded numbers — and a grounding check verifies every number in the
verdict against the brief."

## Scene 7 — 1:00–1:10 — Privacy: on-device only

On-screen (screen recording of the web app):
- "Keep this question on-device only" — ON
- Mode: ONLY_ON_DEVICE
- Your question never leaves this device
- Offline? Quick verdict still works

Say: "Tick one box and the question never leaves your device. On-device
only — no cloud fallback. And offline, the quick verdict still works."

## Scene 8 — 1:10–1:20 — The code

On-screen (code on screen):
- `getGenerativeModel(ai, { mode: InferenceMode.PREFER_ON_DEVICE })`
- `result.response.inferenceSource`
- `→ "ON_DEVICE" or "IN_CLOUD"`
- All AI inference goes through Firebase AI Logic

Say: "Under the hood it is one call: getGenerativeModel with
prefer-on-device. The response tells the app where it ran — on-device or
in cloud. No other model API is called anywhere."

## Scene 9 — 1:20–1:30 — Close

On-screen:
- CMC HYBRID BRIEFS
- On-device when it can · Cloud when it must
- Free tiers: CMC Basic + Firebase free tier
- Repo + live demo in the description

Say: "CMC Hybrid Briefs. On-device when it can, cloud when it must.
Repo and live demo are in the description."

## Shot list for the re-record (cheng, before uploading)

1. Scenes 4–7 must be real screen recordings of the web app running in
   Chrome with your Firebase project configured (not the Remotion text
   cards). Run `python -m cmc_agent.server`, open http://localhost:8765.
2. Scene 5: ask a question with "Quick verdict" selected; point at the
   green "ran on-device" badge.
3. Scene 6: switch to "Deep brief"; point at the "ran in cloud" badge and
   the grounding-check line.
4. Scene 7: tick "Keep this question on-device only" and show the
   `ONLY_ON_DEVICE` routing line.
5. If Gemini Nano is not available on the recording machine, the quick
   verdict falls back to cloud and the badge will say "ran in cloud" —
   say so on camera instead of faking the badge; the fallback is part of
   the hybrid design.
