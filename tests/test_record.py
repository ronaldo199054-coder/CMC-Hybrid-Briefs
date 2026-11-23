"""Tests for the Agent ID receipt command. No network, no keys, no signing.

Run: python -m unittest discover -s tests -v
"""

import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cmc_agent.cli import main  # noqa: E402
from cmc_agent.keccak import keccak256  # noqa: E402
from cmc_agent.record import (  # noqa: E402
    RecordError,
    check_holds_agent_id,
    encode_holds_agent_id_calldata,
    encode_record_calldata,
    query_hash,
    validate_symbol,
)


class TestKeccak(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(
            keccak256(b"").hex(),
            "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470")

    def test_abc(self):
        self.assertEqual(
            keccak256(b"abc").hex(),
            "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45")

    def test_hello_world(self):
        self.assertEqual(
            keccak256(b"hello world").hex(),
            "47173285a8d7341e5e972fc677286384f802f8ef42a5ec5f03bbfa254cb01fad")


class TestRecordEncoding(unittest.TestCase):
    def test_query_hash_is_keccak(self):
        self.assertEqual(query_hash("brief BTC"), keccak256(b"brief BTC"))

    def test_calldata_layout(self):
        qhash = bytes(range(32))
        data = encode_record_calldata(qhash, "BTC")
        # selector (4) + bytes32 (32) + offset (32) + len (32) + "BTC" padded (32)
        self.assertEqual(len(data), 132)
        self.assertEqual(data[4:36], qhash)
        self.assertEqual(int.from_bytes(data[36:68], "big"), 64)
        self.assertEqual(int.from_bytes(data[68:100], "big"), 3)
        self.assertEqual(data[100:103], b"BTC")
        self.assertEqual(data[103:], b"\x00" * 29)

    def test_selector_matches_keccak_of_signature(self):
        data = encode_record_calldata(bytes(32), "BTC")
        self.assertEqual(data[:4], keccak256(b"recordQuery(bytes32,string)")[:4])

    def test_holds_calldata(self):
        data = encode_holds_agent_id_calldata("0x" + "11" * 20)
        self.assertEqual(len(data), 36)
        self.assertEqual(data[:4], keccak256(b"holdsAgentId(address)")[:4])
        self.assertEqual(data[4:], b"\x00" * 12 + b"\x11" * 20)

    def test_symbol_validation(self):
        self.assertEqual(validate_symbol(" btc "), "BTC")
        with self.assertRaises(RecordError):
            validate_symbol("")
        with self.assertRaises(RecordError):
            validate_symbol("A" * 17)


class TestCheckHoldsAgentId(unittest.TestCase):
    def _fake_urlopen(self, result_hex):
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "result": result_hex}).encode()

        class Resp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return body

        return Resp()

    def test_true_and_false(self):
        contract = "0x" + "22" * 20
        addr = "0x" + "33" * 20
        with mock.patch("cmc_agent.record.urllib.request.urlopen",
                        return_value=self._fake_urlopen("0x" + "00" * 31 + "01")):
            self.assertTrue(check_holds_agent_id("https://rpc.example", contract, addr))
        with mock.patch("cmc_agent.record.urllib.request.urlopen",
                        return_value=self._fake_urlopen("0x" + "00" * 32)):
            self.assertFalse(check_holds_agent_id("https://rpc.example", contract, addr))


class TestRecordCli(unittest.TestCase):
    def test_dry_run_no_contract(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["record", "BTC", "--query", "brief BTC"])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("queryHash (keccak256): 0x" + query_hash("brief BTC").hex(), out)
        self.assertIn("not deployed yet", out)
        self.assertIn("Call data: 0x", out)

    def test_check_without_contract_fails(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["record", "BTC", "--check", "0x" + "44" * 20])
        self.assertEqual(code, 1)

    def test_symbol_too_long_fails(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["record", "A" * 17])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
