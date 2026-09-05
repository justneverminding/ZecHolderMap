"""Tests for the private ingestion CLI."""
import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from helpers import DatabaseTestCase

import database
import ingest_receipt


class IngestReceiptTest(DatabaseTestCase):
    def run_cli(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", ["ingest_receipt", *args]), redirect_stdout(stdout), redirect_stderr(stderr):
            code = ingest_receipt.main()
        return code, stdout.getvalue(), stderr.getvalue()

    def test_records_valid_receipt(self):
        code, out, _ = self.run_cli("--receipt-id", "r1", "--memo", "HOLDERMAP:NG")
        self.assertEqual(code, 0)
        self.assertIn("Recorded", out)

    def test_ignores_duplicate_receipt(self):
        self.run_cli("--receipt-id", "r1", "--memo", "HOLDERMAP:NG")
        code, out, _ = self.run_cli("--receipt-id", "r1", "--memo", "HOLDERMAP:NG")
        self.assertEqual(code, 0)
        self.assertIn("Ignored duplicate", out)

    def test_rejects_bad_memo_with_nonzero_exit(self):
        code, _, err = self.run_cli("--receipt-id", "r2", "--memo", "HOLDERMAP:ZZ")
        self.assertEqual(code, 2)
        self.assertIn("Rejected", err)

    def test_missing_arguments_exit_nonzero(self):
        with self.assertRaises(SystemExit) as exc:
            self.run_cli()
        self.assertEqual(exc.exception.code, 2)

    def test_ingested_receipts_flow_into_public_data(self):
        for i in range(database.DISPLAY_THRESHOLD):
            self.run_cli("--receipt-id", f"r{i}", "--memo", "HOLDERMAP:NG")
        ng = next(r for r in database.public_regions() if r["code"] == "NG")
        self.assertEqual(ng["count"], database.DISPLAY_THRESHOLD)


if __name__ == "__main__":
    unittest.main()