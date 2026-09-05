"""Integration tests for the aggregate-only API server."""
import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from helpers import DatabaseTestCase

import database
import server


class ApiServerTest(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.httpd.server_port}"

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)
        super().tearDown()

    def seed(self, counts):
        for code, count in counts.items():
            for i in range(count):
                database.record_receipt(f"{self.id()}-{code}-{i}", f"HOLDERMAP:{code}")

    def get_json(self, path):
        with urllib.request.urlopen(self.base + path) as response:
            return json.load(response)

    def test_map_returns_only_visible_regions(self):
        self.seed({"NG": database.DISPLAY_THRESHOLD, "BR": database.DISPLAY_THRESHOLD - 1})
        payload = self.get_json("/api/map")
        codes = {region["code"] for region in payload["regions"]}
        self.assertEqual(codes, {"NG"})

    def test_map_counts_match_records(self):
        self.seed({"NG": database.DISPLAY_THRESHOLD + 2})
        payload = self.get_json("/api/map")
        self.assertEqual(payload["regions"][0]["count"], database.DISPLAY_THRESHOLD + 2)

    def test_map_exposes_display_threshold(self):
        payload = self.get_json("/api/map")
        self.assertEqual(payload["displayThreshold"], database.DISPLAY_THRESHOLD)

    def test_stats_are_aggregate_only(self):
        self.seed({"NG": database.DISPLAY_THRESHOLD, "CA": database.DISPLAY_THRESHOLD - 1})
        stats = self.get_json("/api/stats")
        self.assertEqual(stats["totalSignals"], database.DISPLAY_THRESHOLD)
        self.assertEqual(stats["countriesRepresented"], 1)

    def test_unknown_api_path_is_404(self):
        with self.assertRaises(urllib.error.HTTPError) as exc:
            self.get_json("/api/nope")
        self.assertEqual(exc.exception.code, 404)

    def test_root_serves_static_site(self):
        with urllib.request.urlopen(self.base + "/") as response:
            body = response.read().decode("utf-8")
        self.assertEqual(response.status, 200)
        self.assertIn("ZEC Holder Map", body)


if __name__ == "__main__":
    unittest.main()