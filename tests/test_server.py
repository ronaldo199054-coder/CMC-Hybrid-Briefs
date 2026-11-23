"""Tests for the local demo server (mock mode, no network, no key).

Starts the real HTTP server on an ephemeral localhost port and checks
the data + hybrid-preview endpoints end to end.
"""

import http.client
import json
import threading
import unittest

from cmc_agent.client import CMCClient
from cmc_agent.server import make_handler
from http.server import ThreadingHTTPServer


class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        client = CMCClient(mock=True)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(client))
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _get(self, path):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.request("GET", path)
        resp = conn.getresponse()
        body = resp.read()
        conn.close()
        return resp.status, body

    def test_index_serves_web_app(self):
        status, body = self._get("/")
        self.assertEqual(status, 200)
        self.assertIn(b"Firebase AI Logic", body)
        self.assertIn(b"CMC Hybrid Briefs", body)

    def test_app_js_imports_firebase_ai_logic(self):
        status, body = self._get("/app.js")
        self.assertEqual(status, 200)
        self.assertIn(b"firebase-ai.js", body)
        self.assertIn(b"getGenerativeModel", body)
        self.assertIn(b"InferenceMode", body)
        self.assertIn(b"inferenceSource", body)

    def test_brief_endpoint_mock(self):
        status, body = self._get("/api/brief?symbol=BTC")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertTrue(data["mock"])
        self.assertIn("Bitcoin", data["brief"])
        self.assertTrue(data["evidence"])

    def test_hybrid_preview_routes_quick_verdict_on_device(self):
        status, body = self._get("/api/hybrid-preview?symbol=BTC&feature=quick_verdict")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertEqual(data["mode"], "PREFER_ON_DEVICE")
        self.assertIn("ONLY the numbers in the brief", data["prompt"])

    def test_hybrid_preview_private_forces_on_device_only(self):
        status, body = self._get("/api/hybrid-preview?symbol=BTC&feature=deep_brief&private=1")
        data = json.loads(body)
        self.assertEqual(data["mode"], "ONLY_ON_DEVICE")

    def test_ask_endpoint(self):
        status, body = self._get("/api/ask?q=is%20BTC%20overheated%20right%20now")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertEqual(data["intent"], "overheated")

    def test_unknown_api_path_404(self):
        status, _ = self._get("/api/nope")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
