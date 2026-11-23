"""Tests for the CMC research agent. All tests run in mock mode —
no API key, no network. Run: python -m unittest discover -s tests -v
"""

import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cmc_agent import brief as brief_mod  # noqa: E402
from cmc_agent.brief import estimated_flow, fmt_pct, fmt_usd  # noqa: E402
from cmc_agent.cli import main  # noqa: E402
from cmc_agent.client import CMCClient, CMCError, load_dotenv  # noqa: E402
from cmc_agent.intents import detect_days, detect_symbol, parse_question  # noqa: E402
from cmc_agent.mock_data import MOCK_BY_SYMBOL, MOCK_GLOBAL, MOCK_LISTINGS  # noqa: E402


def run_cli(argv):
    """Run the CLI in mock mode and return (exit_code, stdout)."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = main(["--mock", *argv])
    return code, buf.getvalue()


class TestIntents(unittest.TestCase):
    def test_gainers(self):
        intent, params = parse_question("top gainers with real volume this week")
        self.assertEqual(intent, "gainers")
        self.assertEqual(params["days"], 7)

    def test_gainers_24h(self):
        intent, params = parse_question("biggest gainers in the past 24h")
        self.assertEqual(intent, "gainers")
        self.assertEqual(params["days"], 1)

    def test_flows(self):
        intent, _ = parse_question("which top-20 coins had the biggest 7d inflows")
        self.assertEqual(intent, "flows")

    def test_overheated(self):
        intent, params = parse_question("is BTC overheated right now")
        self.assertEqual(intent, "overheated")
        self.assertEqual(params["symbol"], "BTC")

    def test_overheated_default_symbol(self):
        intent, params = parse_question("is the market overheated")
        self.assertEqual(intent, "overheated")
        self.assertEqual(params["symbol"], "BTC")

    def test_market(self):
        intent, _ = parse_question("what is the total market cap and BTC dominance")
        self.assertEqual(intent, "market")

    def test_top_n(self):
        intent, params = parse_question("show me the top 5 coins")
        self.assertEqual(intent, "top")
        self.assertEqual(params["limit"], 5)

    def test_brief_by_name(self):
        intent, params = parse_question("tell me about solana")
        self.assertEqual(intent, "brief")
        self.assertEqual(params["symbol"], "SOL")

    def test_default_is_overview(self):
        intent, _ = parse_question("what is going on")
        self.assertEqual(intent, "overview")

    def test_detect_days(self):
        self.assertEqual(detect_days("over the last month"), 30)
        self.assertEqual(detect_days("this week"), 7)
        self.assertEqual(detect_days("today"), 1)
        self.assertEqual(detect_days("no window here"), 7)

    def test_detect_symbol(self):
        self.assertEqual(detect_symbol("how is bitcoin doing"), "BTC")
        self.assertEqual(detect_symbol("ETH price"), "ETH")
        self.assertIsNone(detect_symbol("nothing here"))


class TestFormatting(unittest.TestCase):
    def test_fmt_usd(self):
        self.assertEqual(fmt_usd(1_940_000_000_000), "$1.94T")
        self.assertEqual(fmt_usd(38_200_000_000), "$38.20B")
        self.assertEqual(fmt_usd(1_500_000), "$1.50M")
        self.assertEqual(fmt_usd(None), "n/a")

    def test_fmt_pct(self):
        self.assertEqual(fmt_pct(4.2), "+4.2%")
        self.assertEqual(fmt_pct(-6.5), "-6.5%")
        self.assertEqual(fmt_pct(0), "0.0%")

    def test_estimated_flow(self):
        # mcap 1000, +10% -> flow = 1000 * 0.1 / 1.1 = 90.9
        self.assertAlmostEqual(estimated_flow(1000, 10), 90.909, places=2)
        self.assertIsNone(estimated_flow(None, 10))
        self.assertIsNone(estimated_flow(1000, None))


class TestBriefs(unittest.TestCase):
    def test_brief_coin_has_numbers(self):
        text = brief_mod.brief_coin(MOCK_BY_SYMBOL["BTC"])
        self.assertIn("Bitcoin (BTC)", text)
        self.assertIn("$97,420.00", text)
        self.assertIn("+4.2%", text)
        self.assertIn("Verdict:", text)
        self.assertIn("not investment advice", text)

    def test_brief_coin_bounce_verdict(self):
        # BTC mock: 7d +4.2, 30d -6.5 -> bounce wording
        text = brief_mod.brief_coin(MOCK_BY_SYMBOL["BTC"])
        self.assertIn("bounce", text)

    def test_gainers_excludes_stables(self):
        text = brief_mod.gainers_brief(MOCK_LISTINGS, 7)
        for stable in ("USDT", "USDC", "STETH", "WBTC"):
            self.assertNotIn(f"  {stable} ", text)
        self.assertIn("DOGE", text)  # mock 7d leader
        self.assertIn("Verdict:", text)

    def test_gainers_sorted_desc(self):
        text = brief_mod.gainers_brief(MOCK_LISTINGS, 7)
        self.assertLess(text.index("DOGE"), text.index("SOL"))

    def test_flows_labels_estimate(self):
        text = brief_mod.flows_brief(MOCK_LISTINGS, 7)
        self.assertIn("estimated", text.lower())
        self.assertIn("BTC", text)
        self.assertIn("Verdict:", text)

    def test_market_brief(self):
        text = brief_mod.market_brief(MOCK_GLOBAL)
        self.assertIn("$3.42T", text)
        self.assertIn("56.8%", text)
        self.assertIn("Verdict:", text)

    def test_overheated_thresholds(self):
        hot = dict(MOCK_BY_SYMBOL["DOGE"])  # 7d +12.4, 30d -14.1 -> warming up
        text = brief_mod.overheated_brief(hot)
        self.assertIn("Warming up", text)
        cool = dict(MOCK_BY_SYMBOL["AVAX"])  # 7d -7.3 -> not overheated
        self.assertIn("Not overheated", brief_mod.overheated_brief(cool))
        # Synthetic blow-off: 7d +20, 30d +60
        blow = {
            "name": "Testcoin", "symbol": "TEST",
            "quote": {"USD": {"percent_change_7d": 20.0, "percent_change_30d": 60.0, "percent_change_90d": 120.0}},
        }
        self.assertIn("Running hot", brief_mod.overheated_brief(blow))


class TestMockClient(unittest.TestCase):
    def setUp(self):
        self.client = CMCClient(mock=True)

    def test_listings(self):
        rows = self.client.listings_latest(limit=20)
        self.assertEqual(len(rows), 20)
        self.assertEqual(rows[0]["symbol"], "BTC")
        self.assertEqual(self.client.calls[0]["endpoint"], "/cryptocurrency/listings/latest")

    def test_quotes(self):
        coin = self.client.quotes_latest("btc")
        self.assertEqual(coin["symbol"], "BTC")
        self.assertAlmostEqual(coin["quote"]["USD"]["price"], 97420.0)

    def test_unknown_symbol_raises(self):
        with self.assertRaises(CMCError):
            self.client.quotes_latest("NOTACOIN")

    def test_global_metrics(self):
        g = self.client.global_metrics()
        self.assertAlmostEqual(g["quote"]["USD"]["btc_dominance"], 56.8)

    def test_key_info_free(self):
        info = self.client.key_info()
        self.assertEqual(info["plan"]["name"], "Basic")
        self.assertEqual(self.client.calls[-1]["credits"], 0)

    def test_evidence_lists_calls(self):
        self.client.listings_latest(limit=10)
        self.client.global_metrics()
        lines = self.client.evidence_lines()
        joined = "\n".join(lines)
        self.assertIn("MOCK", joined)
        self.assertIn("/cryptocurrency/listings/latest", joined)
        self.assertIn("/global-metrics/quotes/latest", joined)
        self.assertIn("Total credits used:", joined)


class TestCLI(unittest.TestCase):
    def test_ask_gainers(self):
        code, out = run_cli(["ask", "top gainers with real volume this week"])
        self.assertEqual(code, 0)
        self.assertIn("Top gainers", out)
        self.assertIn("[mock]", out)
        self.assertIn("API calls made", out)

    def test_ask_flows(self):
        code, out = run_cli(["ask", "which top-20 coins had the biggest 7d inflows"])
        self.assertEqual(code, 0)
        self.assertIn("flows", out.lower())
        self.assertIn("estimated", out.lower())

    def test_ask_overheated(self):
        code, out = run_cli(["ask", "is BTC overheated right now"])
        self.assertEqual(code, 0)
        self.assertIn("overheated check", out)

    def test_brief(self):
        code, out = run_cli(["brief", "btc"])
        self.assertEqual(code, 0)
        self.assertIn("Bitcoin (BTC)", out)

    def test_gainers_cmd(self):
        code, out = run_cli(["gainers"])
        self.assertEqual(code, 0)
        self.assertIn("DOGE", out)

    def test_flows_cmd(self):
        code, out = run_cli(["flows"])
        self.assertEqual(code, 0)
        self.assertIn("BTC", out)

    def test_market_cmd(self):
        code, out = run_cli(["market"])
        self.assertEqual(code, 0)
        self.assertIn("Market overview", out)

    def test_status_cmd(self):
        code, out = run_cli(["status"])
        self.assertEqual(code, 0)
        self.assertIn("Basic", out)
        self.assertIn("15,000", out)

    def test_unknown_symbol_exits_nonzero(self):
        code, out = run_cli(["brief", "notacoin"])
        self.assertNotEqual(code, 0)

    def test_key_never_printed(self):
        os.environ["CMC_API_KEY"] = "SECRETKEY123"
        try:
            code, out = run_cli(["brief", "btc"])
        finally:
            del os.environ["CMC_API_KEY"]
        self.assertEqual(code, 0)
        self.assertNotIn("SECRETKEY123", out)


class TestDotenv(unittest.TestCase):
    def test_load_dotenv_sets_key(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text("CMC_API_KEY=dotenv-test-key\n", encoding="utf-8")
            os.environ.pop("CMC_API_KEY", None)
            try:
                load_dotenv(env_path)
                self.assertEqual(os.environ.get("CMC_API_KEY"), "dotenv-test-key")
            finally:
                os.environ.pop("CMC_API_KEY", None)


if __name__ == "__main__":
    unittest.main()
