"""Shared fixtures: point the backend at a fresh temporary database per test."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import database


class DatabaseTestCase(unittest.TestCase):
    """Redirects the backend's SQLite database to a temp file for each test."""

    def setUp(self):
        self._tempdir = tempfile.TemporaryDirectory()
        self._original_path = database.DATABASE_PATH
        database.DATABASE_PATH = Path(self._tempdir.name) / "holdermap.sqlite"

    def tearDown(self):
        database.DATABASE_PATH = self._original_path
        self._tempdir.cleanup()