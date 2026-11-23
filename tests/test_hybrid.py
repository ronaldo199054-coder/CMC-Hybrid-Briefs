"""Tests for the hybrid routing policy and grounded prompts.

No network, no Firebase, no model call: routing and prompts are pure
functions over the deterministic brief.
"""

import unittest

from cmc_agent.hybrid import (
    ONLY_IN_CLOUD,
    ONLY_ON_DEVICE,
    PREFER_IN_CLOUD,
    PREFER_ON_DEVICE,
    build_grounded_prompt,
    check_grounding,
    route_feature,
)

BRIEF = (
    "Bitcoin (BTC) — rank #1\n"
    "Price: $97,500.00 | 24h: +2.3% | 7d: +5.1% | 30d: -8.0%\n"
    "Market cap: $1.93T | 24h volume: $45.20B\n"
    "Verdict: up 5.1% over 7 days after a 8.0% drop over 30 days."
)


class TestRouting(unittest.TestCase):
    def test_quick_verdict_prefers_on_device(self):
        self.assertEqual(route_feature("quick_verdict"), PREFER_ON_DEVICE)

    def test_deep_brief_prefers_cloud(self):
        self.assertEqual(route_feature("deep_brief"), PREFER_IN_CLOUD)

    def test_private_forces_on_device_only(self):
        self.assertEqual(route_feature("quick_verdict", private=True), ONLY_ON_DEVICE)
        self.assertEqual(route_feature("deep_brief", private=True), ONLY_ON_DEVICE)

    def test_offline_quick_verdict_stays_on_device(self):
        self.assertEqual(route_feature("quick_verdict", online=False), ONLY_ON_DEVICE)

    def test_offline_deep_brief_is_unavailable_not_guessed(self):
        with self.assertRaises(RuntimeError):
            route_feature("deep_brief", online=False)

    def test_unknown_feature_rejected(self):
        with self.assertRaises(ValueError):
            route_feature("chat")

    def test_mode_names_match_firebase_ai_logic_sdk(self):
        self.assertEqual(PREFER_ON_DEVICE, "PREFER_ON_DEVICE")
        self.assertEqual(ONLY_ON_DEVICE, "ONLY_ON_DEVICE")
        self.assertEqual(PREFER_IN_CLOUD, "PREFER_IN_CLOUD")
        self.assertEqual(ONLY_IN_CLOUD, "ONLY_IN_CLOUD")


class TestGroundedPrompt(unittest.TestCase):
    def test_prompt_contains_the_brief_verbatim(self):
        prompt = build_grounded_prompt(BRIEF, question="brief BTC")
        self.assertIn(BRIEF, prompt)
        self.assertIn("brief BTC", prompt)

    def test_prompt_forbids_invented_numbers(self):
        prompt = build_grounded_prompt(BRIEF)
        self.assertIn("ONLY the numbers in the brief below", prompt)
        self.assertIn("Do not invent", prompt)

    def test_prompt_ends_with_advice_disclaimer_rule(self):
        prompt = build_grounded_prompt(BRIEF)
        self.assertIn("Not investment advice.", prompt)

    def test_empty_brief_rejected(self):
        with self.assertRaises(ValueError):
            build_grounded_prompt("   ")


class TestGroundingCheck(unittest.TestCase):
    def test_numbers_from_brief_are_clean(self):
        ai = "BTC is up 5.1% over 7 days at $97,500.00."
        self.assertEqual(check_grounding(ai, BRIEF), [])

    def test_invented_number_is_flagged(self):
        ai = "BTC is up 5.1% and could hit $150,000.00 next week."
        self.assertIn("150000.00", check_grounding(ai, BRIEF))

    def test_no_numbers_no_flags(self):
        self.assertEqual(check_grounding("No numbers here.", BRIEF), [])


if __name__ == "__main__":
    unittest.main()
