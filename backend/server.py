#!/usr/bin/env python3
"""Serves the static prototype and aggregate-only API for local testnet work."""
import json
import os
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from database import DISPLAY_THRESHOLD, initialize, public_regions, public_stats

ROOT = Path(__file__).resolve().parent.parent
HOST = os.environ.get("HOLDER_MAP_HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "4173"))


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/map":
            return self.json({"regions": public_regions(), "displayThreshold": DISPLAY_THRESHOLD})
        if path == "/api/stats":
            return self.json(public_stats())
        return super().do_GET()

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def json(self, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    initialize()
    print(f"Holder Map backend: http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
