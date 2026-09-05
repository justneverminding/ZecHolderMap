"""Private storage for Holder Map receipt aggregation."""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List

DISPLAY_THRESHOLD = 5
DATABASE_PATH = Path(os.environ.get("HOLDER_MAP_DATABASE", Path(__file__).parent / "storage" / "holdermap.sqlite"))

# ISO 3166-1 alpha-2 codes. Memos are deliberately restricted to this finite set.
COUNTRY_CODES = frozenset("""
AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ
CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO FR
GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO JP
KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT
MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO RS RU RW
SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF TG TH TJ TK TL TM TN TO TR TT TV TW TZ UA UG
UM US UY UZ VA VC VE VG VI VN VU WF WS YE YT ZA ZM ZW
""".split())


def connect() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def initialize() -> None:
    with connect() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS processed_receipts (
                receipt_id TEXT PRIMARY KEY,
                region_code TEXT NOT NULL,
                received_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS region_counts (
                region_code TEXT PRIMARY KEY,
                count INTEGER NOT NULL DEFAULT 0 CHECK (count >= 0)
            );
            """
        )


def parse_memo(memo: str) -> str:
    prefix = "HOLDERMAP:"
    if not memo.startswith(prefix):
        raise ValueError("Memo must start with HOLDERMAP:")
    region = memo[len(prefix):]
    if region not in COUNTRY_CODES:
        raise ValueError("Memo must contain a valid uppercase ISO country code")
    return region


def record_receipt(receipt_id: str, memo: str) -> bool:
    """Record one valid receipt. Returns False for an already-processed receipt."""
    if not receipt_id or len(receipt_id) > 256:
        raise ValueError("Receipt identifier is required")
    region = parse_memo(memo)
    initialize()
    with connect() as db:
        try:
            db.execute("INSERT INTO processed_receipts (receipt_id, region_code) VALUES (?, ?)", (receipt_id, region))
        except sqlite3.IntegrityError:
            return False
        db.execute(
            """INSERT INTO region_counts (region_code, count) VALUES (?, 1)
               ON CONFLICT(region_code) DO UPDATE SET count = count + 1""",
            (region,),
        )
    return True


def public_regions() -> List[Dict[str, int]]:
    initialize()
    with connect() as db:
        rows = db.execute(
            "SELECT region_code, count FROM region_counts WHERE count >= ? ORDER BY count DESC, region_code", (DISPLAY_THRESHOLD,)
        ).fetchall()
    return [{"code": row["region_code"], "count": row["count"]} for row in rows]


def public_stats() -> Dict[str, int]:
    regions = public_regions()
    return {"totalSignals": sum(region["count"] for region in regions), "countriesRepresented": len(regions), "displayThreshold": DISPLAY_THRESHOLD}
