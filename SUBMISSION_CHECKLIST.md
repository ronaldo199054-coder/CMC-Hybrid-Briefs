# Submission checklist — #BuildHybridAI 2026

Official page: https://firebasehybridaihackathon.devpost.com/
Official rules / FAQ (verified 2026-11-23):
https://firebasehybridaihackathon.devpost.com/details/faqs

## Verified facts (from the official FAQ)

| Item | Value |
|---|---|
| Submissions open | Nov 11, 2026, 1:30 PM PT |
| **Submission deadline** | **Mon Nov 30, 2026, 2:00 PM PT = Dec 1, 2026, 06:00 Beijing** (fixed, no extension; commits after the deadline are not evaluated) |
| Judging | Dec 10–16; winners announced on/around Mon Dec 21, 12:00 PM PT |
| Total prizes | **$30,000** — Grand Prize $10,000 (+ interview, blog post, social mention); 1st Runner-Up $7,000; 2nd Runner-Up $4,000; $3,000 each for Best iOS, Best Android, Best Web/Chrome. One grand prize + at most one "Best of" prize per project |
| Eligible platforms | Web (Chrome, incl. Chrome extension) with Gemini Nano 4; Android with Gemini Nano 4; iOS with Apple Foundation Models — all via Firebase AI Logic. **This entry: Web (Chrome)** |
| Eligibility | Above the age of majority where you live; residence-based. **Excluded residences: Brazil, Italy, Quebec, Crimea, Cuba, Iran, Syria, North Korea, Sudan, Belarus, Russia, OFAC-sanctioned countries. Mainland China is NOT excluded.** Google/Devpost employees, contractors, government employees and their immediate families are excluded |
| Entry type | Individual, team, or organization. No purchase necessary |
| Quota Sprint 3 (final) | **Request by Wed Nov 25, 10:00 AM PT = Nov 26, 02:00 Beijing** (sent Fri Nov 27). One account per entrant, per project, per sprint. Only needed if a billing-required model is used |

## Submission form — exact fields to fill (Devpost)

1. **Title:** CMC Hybrid Briefs
2. **Tagline / one-liner:** Plain-language crypto briefs from live
   CoinMarketCap data — AI verdicts that run on-device when they can and
   in the cloud when they must, all through Firebase AI Logic.
3. **Platform (select at least one):** Web (Chrome).
4. **Description — how you used Firebase AI Logic:** Quick verdict uses
   `getGenerativeModel(ai, { mode: InferenceMode.PREFER_ON_DEVICE })`
   (Gemini Nano 4 on Chrome, cloud fallback); deep brief uses
   `PREFER_IN_CLOUD` with cloud model `gemini-3.5-flash-lite` (Google's
   designated replacement for the deprecated `gemini-2.5-flash`); "keep
   on-device" uses `ONLY_ON_DEVICE`. The verdict's
   `response.inferenceSource` is shown as an ON_DEVICE / IN_CLOUD badge.
   Firebase App Check is enabled (required). All AI inference goes
   through Firebase AI Logic; the Python server only serves CoinMarketCap
   data and the grounded prompt — it calls no model API.
5. **Description — features & value:** (a) grounded briefs — every number
   comes from live CoinMarketCap data, the model only receives the brief
   verbatim and is told to use only its numbers; (b) hybrid inference per
   feature — fast/private on-device verdicts, deeper cloud briefs;
   (c) privacy toggle — a question can be kept on-device only, and the
   quick verdict works offline; (d) transparency — evidence block (every
   CMC call + credits) and a grounding check that flags numbers not in
   the brief. For retail crypto readers who get invented numbers from
   chatbots and do not want every question sent to a server.
6. **Public repo URL:** [cheng to fill in — see "What cheng must do"]
7. **Demo video URL (YouTube, ≤3 min, English):** [cheng to fill in after
   uploading — script in `DEMO_VIDEO_SCRIPT.md`, render in `demo-video/`]
8. **Working project URL (strongly encouraged, optional):** [optional —
   deploy `web/` + server, or leave blank; judges may judge on the video
   + description alone. If testing needs a login, put test credentials in
   the testing instructions; never include production keys]
9. **Built during the submission period (existing app):** This adapts the
   author's own `cmc-agent` CLI (built Nov 18–19, 2026 for the Build with
   CMC hackathon). New work for this hackathon: the whole `web/` app,
   Firebase AI Logic integration, `cmc_agent/hybrid.py` (routing +
   grounded prompts + grounding guard), `cmc_agent/server.py`, the
   `hybrid` CLI command, and their tests. Reused: CMC data client,
   deterministic briefs, intent parsing, receipt contract. See README
   "Submission — pre-existing code disclosure".
10. **Testing instructions:** `pip install -r requirements.txt`, copy
    `.env.example` to `.env` and add a free CMC key (or run with
    `--mock` for labeled mock data), copy
    `web/firebase-config.example.js` to `web/firebase-config.js` with
    Firebase project values, run `python -m cmc_agent.server`, open
    http://localhost:8765 in Chrome (enable
    `chrome://flags/#prompt-api-for-gemini-nano-multimodal-input` for
    on-device Nano). Or run the CLI: `python -m cmc_agent hybrid btc`.

## Repo requirements (check before submitting)

- [ ] Public GitHub or GitLab repo, with an **open-source license file
      visible in the repo's About section** (this repo: MIT, `LICENSE`).
- [ ] Repo includes all source code, assets, and run instructions
      (`README.md`).
- [ ] **Firebase AI Logic is imported and actually called at runtime, not
      just named in the README** — `web/app.js` imports `firebase/ai`
      and calls `getGenerativeModel` + `generateContent`. Verify the
      import is in the committed code.
- [ ] **No secrets in the repo:** no `.env`, no `web/firebase-config.js`,
      no App Check debug token, no service-account key. Both are
      git-ignored; check `git status` before pushing.
- [ ] Demo video ≤3 min, public on YouTube, in English (or with English
      subtitles), showing the project working on Web/Chrome. Upload early
      — processing can take hours.

## What cheng must do himself (Muse does not do these)

1. **Register for the hackathon on Devpost** (if not done) — account +
   entry are yours; Muse never registers, submits, or posts for you.
2. **Firebase project:** create it in the Firebase console, enable
   Firebase AI Logic (Gemini Developer API backend) and App Check; fill
   in `web/firebase-config.js` from the example. For local dev, use an
   App Check debug token; for any public deployment, use reCAPTCHA v3.
3. **Quota (only if needed):** check the Firebase AI Logic models list —
   if the cloud model you use is marked "billing required", request a
   Google Account Quota via https://forms.gle/uPcDhaYW3iVo2AYw5 by
   **Nov 25, 10:00 AM PT = Nov 26, 02:00 Beijing** (Sprint 3, final).
   Register for the hackathon first. Text inference on the free tier
   needs no purchase.
4. **CMC API key:** get a free key at https://pro.coinmarketcap.com/signup/
   and put it in this folder's own `.env` (`chmod 600 .env`). Do NOT copy
   the `.env` from the original cmc-agent repo.
5. **GitHub repo:** create a public repo (e.g. `cmc-hybrid-briefs`), push
   this folder, confirm the MIT license shows in the repo About section.
6. **Test the live app yourself:** run the server, ask a question in
   Chrome, confirm the on-device badge appears (or the cloud fallback
   with an honest note if Nano is unavailable on that machine).
7. **Demo video:** re-record scenes 4–7 with the real app (see shot list
   in `DEMO_VIDEO_SCRIPT.md`), upload the ≤3 min video to YouTube as
   public, and paste the link in the submission form.
8. **Submit on Devpost before Dec 1, 06:00 Beijing** (Nov 30, 2:00 PM PT).
   You can edit and save drafts until then; after the deadline the
   submission is locked and later commits are not evaluated.
9. **Do NOT touch the `cmc-agent` main branch** — it is the submitted
   entry for CMC Round 2 and the Binance Agent ID Hackathon. This entry
   lives only in `~/workspace/hackathon-entries/buildhybridai/`.

## Blocked / unverified items

- **Live on-device inference not yet verified end-to-end:** the web app's
  Firebase AI Logic calls are real code, but no Firebase project exists
  yet and this machine has no Chrome with Gemini Nano, so the
  `PREFER_ON_DEVICE` -> `ON_DEVICE` path has not been run live. It is
  verified by code inspection + docs + unit tests only. Cheng must create
  the Firebase project and test in Chrome (step 6 above).
- **Whether the cloud model is "billing required":** resolved 2026-11-23 —
  `gemini-3.5-flash-lite` replaced the deprecated `gemini-2.5-flash` in
  code, config and docs. On the Gemini Developer API backend it is a
  stable text model on the free tier, so no billing account and no Sprint 3
  quota request are needed (billing would only be required on the Agent
  Platform / Vertex AI backend). The Nov 26, 02:00 Beijing Sprint 3
  deadline no longer applies to this entry as configured. The old
  `gemini-2.5-flash` string would also have auto-routed to
  `gemini-3.5-flash-lite` from Dec 1, 2026 — during judging — and a
  brand-new Firebase project may not have qualified as a previously
  active 2.5 user, so the switch removes that risk too.
