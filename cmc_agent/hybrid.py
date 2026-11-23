"""Hybrid inference routing policy for the #BuildHybridAI 2026 entry.

This module is the single source of truth for *which* Firebase AI Logic
inference mode each feature uses and *what* gets sent to the model. It
contains no model call: all AI inference happens in the web app
(`web/app.js`) through Firebase AI Logic. The CLI `hybrid` command and the
local server (`/api/hybrid-preview`) only show the routing decision and the
grounded prompt, so the behaviour can be tested without a Firebase project.

Routing (mirrors the Firebase AI Logic JS SDK `InferenceMode` values):
- quick_verdict  -> PREFER_ON_DEVICE  (Gemini Nano 4 on Chrome when
  available, cloud fallback; fast, private, single-turn text)
- deep_brief     -> PREFER_IN_CLOUD   (cloud Gemini model; longer,
  structured explanation the on-device model cannot do well)
- private question (user toggles "keep on device") -> ONLY_ON_DEVICE
  (never leaves the device; throws instead of falling back to cloud)
- offline        -> ONLY_ON_DEVICE for quick verdict; deep brief is
  unavailable offline and the app says so instead of guessing.

Grounding rule: the model only ever receives the deterministic brief
produced by `brief.py` from live CoinMarketCap data. The prompt instructs
it to use ONLY the numbers in that brief, never invent a price, and end
with "not investment advice". `check_grounding()` is a heuristic guard
that flags $- or %-numbers in model output that do not appear in the
brief; the web app shows the flag next to the verdict.
"""

from __future__ import annotations

import re

# Firebase AI Logic InferenceMode names, as used by the JS SDK.
PREFER_ON_DEVICE = "PREFER_ON_DEVICE"
ONLY_ON_DEVICE = "ONLY_ON_DEVICE"
PREFER_IN_CLOUD = "PREFER_IN_CLOUD"
ONLY_IN_CLOUD = "ONLY_IN_CLOUD"

FEATURES = ("quick_verdict", "deep_brief")

# Cloud model used as the explicit fallback for deep briefs.
# Override in web/firebase-config.js if your Firebase project uses another.
# gemini-3.5-flash-lite is Google's designated replacement for the
# deprecated gemini-2.5-flash (auto-routed from Dec 1, 2026); it is a
# current Firebase AI Logic model on the Gemini Developer API free tier.
CLOUD_MODEL = "gemini-3.5-flash-lite"


def route_feature(feature, *, private=False, online=True):
    """Return the Firebase AI Logic inference mode for a feature.

    `feature` is "quick_verdict" or "deep_brief".
    Raises ValueError for an unknown feature, RuntimeError when the
    requested feature cannot run (deep brief needs the cloud).
    """
    if feature not in FEATURES:
        raise ValueError(f"Unknown feature: {feature!r} (expected one of {FEATURES})")
    if private:
        # The user asked that this question never leave the device.
        return ONLY_ON_DEVICE
    if not online:
        if feature == "deep_brief":
            raise RuntimeError(
                "Deep brief needs the cloud model and you are offline. "
                "Use the quick verdict (on-device) instead."
            )
        return ONLY_ON_DEVICE
    if feature == "quick_verdict":
        return PREFER_ON_DEVICE
    return PREFER_IN_CLOUD


def build_grounded_prompt(brief_text, question=None):
    """Build the exact prompt the web app sends to Firebase AI Logic.

    The deterministic CMC brief is pasted verbatim as the only source of
    numbers. The model is told to use only those numbers, to keep the
    answer short, and to add the not-investment-advice line.
    """
    brief_text = (brief_text or "").strip()
    if not brief_text:
        raise ValueError("Cannot build a prompt from an empty brief.")
    q = (question or "").strip()
    lines = [
        "You are a crypto research assistant. Answer in plain English,",
        "in at most 120 words, using ONLY the numbers in the brief below.",
        "Do not invent, round up, or guess any price, percentage, or rank.",
        "If the brief does not contain a number you need, say it is missing.",
        "End with exactly this line: Not investment advice.",
        "",
    ]
    if q:
        lines.append(f"User question: {q}")
        lines.append("")
    lines.append("Brief (live CoinMarketCap data, deterministic summary):")
    lines.append(brief_text)
    return "\n".join(lines)


_NUMBER_RE = re.compile(r"\$[\d,]+(?:\.\d+)?|\b\d+(?:\.\d+)?%")


def _numbers(text):
    """All $- and %-numbers in a text, normalised (no $ , %)."""
    found = []
    for m in _NUMBER_RE.finditer(text or ""):
        found.append(m.group(0).replace("$", "").replace(",", "").replace("%", ""))
    return found


def check_grounding(ai_text, brief_text):
    """Flag numbers in model output that do not appear in the brief.

    Returns a list of ungrounded number strings (empty = clean). This is
    a heuristic, not a proof: a number can be a legitimate restatement
    (e.g. "$1.50K" vs "$1,500"), so the web app shows the flag for the
    user to judge instead of silently dropping the verdict.
    """
    brief_numbers = set(_numbers(brief_text))
    return [n for n in _numbers(ai_text) if n not in brief_numbers]
