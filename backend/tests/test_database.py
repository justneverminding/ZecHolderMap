"""Unit tests for private receipt storage and aggregation."""
import unittest

from helpers import DatabaseTestCase

import database


class ParseMemoTest(DatabaseTestCase):
    def test_valid_country_code_is_accepted(self):
        self.assertEqual(database.parse_memo("HOLDERMAP:NG"), "NG")

    def test_any_iso_code_is_accepted(self):
        self.assertEqual(database.parse_memo("HOLDERMAP:GB"), "GB")

    def test_missing_prefix_is_rejected(self):
        with self.assertRaises(ValueError):
            database.parse_memo("NG")

    def test_lowercase_code_is_rejected(self):
        with self.assertRaises(ValueError):
            database.parse_memo("HOLDERMAP:ng")

    def test_unknown_code_is_rejected(self):
        with self.assertRaises(ValueError):
            database.parse_memo("HOLDERMAP:ZZ")

    def test_trailing_garbage_is_rejected(self):
        with self.assertRaises(ValueError):
            database.parse_memo("HOLDERMAP:NGG")

    def test_empty_region_is_rejected(self):
        with self.assertRaises(ValueError):
            database.parse_memo("HOLDERMAP:")


class RecordReceiptTest(DatabaseTestCase):
    def test_receipts_are_recorded(self):
        self.assertTrue(database.record_receipt("r1", "HOLDERMAP:NG"))
        self.assertTrue(database.record_receipt("r2", "HOLDERMAP:NG"))

    def test_duplicate_receipt_is_ignored(self):
        self.assertTrue(database.record_receipt("r1", "HOLDERMAP:NG"))
        self.assertFalse(database.record_receipt("r1", "HOLDERMAP:NG"))

    def test_duplicate_receipt_does_not_double_count(self):
        for i in range(database.DISPLAY_THRESHOLD):
            database.record_receipt(f"r{i}", "HOLDERMAP:NG")
        self.assertFalse(database.record_receipt("r0", "HOLDERMAP:NG"))
        ng = next(r for r in database.public_regions() if r["code"] == "NG")
        self.assertEqual(ng["count"], database.DISPLAY_THRESHOLD)

    def test_same_receipt_cannot_move_region(self):
        self.assertTrue(database.record_receipt("r1", "HOLDERMAP:NG"))
        self.assertFalse(database.record_receipt("r1", "HOLDERMAP:BR"))
        self.assertEqual(database.public_stats()["totalSignals"], 0)

    def test_regions_accumulate_independently(self):
        for i in range(database.DISPLAY_THRESHOLD):
            database.record_receipt(f"ng-{i}", "HOLDERMAP:NG")
        for i in range(database.DISPLAY_THRESHOLD):
            database.record_receipt(f"br-{i}", "HOLDERMAP:BR")
        stats = database.public_stats()
        self.assertEqual(stats["countriesRepresented"], 2)
        self.assertEqual(stats["totalSignals"], database.DISPLAY_THRESHOLD * 2)

    def test_rejects_missing_receipt_identifier(self):
        with self.assertRaises(ValueError):
            database.record_receipt("", "HOLDERMAP:NG")

    def test_rejects_oversized_receipt_identifier(self):
        with self.assertRaises(ValueError):
            database.record_receipt("x" * 257, "HOLDERMAP:NG")

    def test_rejects_invalid_memo(self):
        with self.assertRaises(ValueError):
            database.record_receipt("r1", "HOLDERMAP:ZZ")

    def test_record_creates_storage_file(self):
        database.record_receipt("r1", "HOLDERMAP:NG")
        self.assertTrue(database.DATABASE_PATH.exists())


class PublicAggregationTest(DatabaseTestCase):
    def seed(self, code, count):
        for i in range(count):
            database.record_receipt(f"{self.id()}-{code}-{i}", f"HOLDERMAP:{code}")

    def test_below_threshold_is_hidden(self):
        self.seed("NG", database.DISPLAY_THRESHOLD - 1)
        self.assertEqual(database.public_regions(), [])

    def test_at_threshold_is_visible(self):
        self.seed("NG", database.DISPLAY_THRESHOLD)
        self.assertEqual(database.public_regions(), [{"code": "NG", "count": database.DISPLAY_THRESHOLD}])

    def test_count_accumulates_above_threshold(self):
        self.seed("NG", database.DISPLAY_THRESHOLD + 2)
        self.assertEqual(database.public_regions(), [{"code": "NG", "count": database.DISPLAY_THRESHOLD + 2}])

    def test_regions_sorted_by_count_desc_then_code(self):
        self.seed("US", database.DISPLAY_THRESHOLD)
        self.seed("NG", database.DISPLAY_THRESHOLD + 2)
        self.seed("BR", database.DISPLAY_THRESHOLD + 1)
        codes = [region["code"] for region in database.public_regions()]
        self.assertEqual(codes, ["NG", "BR", "US"])

    def test_equal_counts_tiebreak_alphabetically(self):
        self.seed("JP", database.DISPLAY_THRESHOLD)
        self.seed("DE", database.DISPLAY_THRESHOLD)
        codes = [region["code"] for region in database.public_regions()]
        self.assertEqual(codes, ["DE", "JP"])

    def test_stats_count_visible_regions_only(self):
        self.seed("NG", database.DISPLAY_THRESHOLD)
        self.seed("CA", database.DISPLAY_THRESHOLD - 1)
        stats = database.public_stats()
        self.assertEqual(stats["totalSignals"], database.DISPLAY_THRESHOLD)
        self.assertEqual(stats["countriesRepresented"], 1)

    def test_stats_expose_display_threshold(self):
        self.assertEqual(database.public_stats()["displayThreshold"], database.DISPLAY_THRESHOLD)

    def test_initialize_is_idempotent(self):
        database.initialize()
        database.initialize()
        self.assertTrue(database.DATABASE_PATH.exists())


if __name__ == "__main__":
    unittest.main()