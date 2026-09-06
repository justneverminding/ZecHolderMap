"""Private storage for Holder Map receipt aggregation.

Backs onto SQLite (local dev, tests) or PostgreSQL (deployments). Pick the engine
with HOLDER_MAP_DATABASE: a plain path means SQLite; a postgres:// URL means
PostgreSQL. All code paths expose the same behaviour.
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse

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


def is_postgres() -> bool:
    return str(DATABASE_PATH).startswith(("postgres://", "postgresql://"))


def pg8000_integrity_error():
    import pg8000.dbapi

    return pg8000.dbapi.IntegrityError


@contextmanager
def connect():
    """Open a connection to whichever engine HOLDER_MAP_DATABASE points at."""
    if is_postgres():
        import pg8000.dbapi as pg

        url = urlparse(str(DATABASE_PATH))
        import ssl

        conn = pg.connect(
            host=url.hostname,
            port=url.port or 5432,
            user=url.username or "",
            password=url.password or "",
            database=url.path.lstrip("/"),
            ssl_context=ssl.create_default_context(),
        )
        try:
            yield conn
        finally:
            conn.close()
    else:
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        try:
            yield conn
        finally:
            conn.close()


SCHEMA = """
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


def _schema_statements():
    return [statement.strip() for statement in SCHEMA.split(";") if statement.strip()]


def initialize() -> None:
    with connect() as db:
        if is_postgres():
            cursor = db.cursor()
            for statement in _schema_statements():
                cursor.execute(statement)
            db.commit()
        else:
            db.executescript(SCHEMA)


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
    duplicate = (pg8000_integrity_error() if is_postgres() else sqlite3.IntegrityError)
    with connect() as db:
        cursor = db.cursor()
        try:
            if is_postgres():
                cursor.execute(
                    "INSERT INTO processed_receipts (receipt_id, region_code) VALUES (%s, %s)",
                    (receipt_id, region),
                )
            else:
                cursor.execute(
                    "INSERT INTO processed_receipts (receipt_id, region_code) VALUES (?, ?)",
                    (receipt_id, region),
                )
        except duplicate:
            db.rollback()
            return False
        if is_postgres():
            cursor.execute(
                """INSERT INTO region_counts (region_code, count) VALUES (%s, 1)
                   ON CONFLICT(region_code) DO UPDATE SET count = region_counts.count + 1""",
                (region,),
            )
        else:
            cursor.execute(
                """INSERT INTO region_counts (region_code, count) VALUES (?, 1)
                   ON CONFLICT(region_code) DO UPDATE SET count = count + 1""",
                (region,),
            )
        db.commit()
    return True


def public_regions() -> List[Dict[str, int]]:
    initialize()
    with connect() as db:
        cursor = db.cursor()
        if is_postgres():
            cursor.execute(
                "SELECT region_code, count FROM region_counts WHERE count >= %s ORDER BY count DESC, region_code",
                (DISPLAY_THRESHOLD,),
            )
        else:
            cursor.execute(
                "SELECT region_code, count FROM region_counts WHERE count >= ? ORDER BY count DESC, region_code",
                (DISPLAY_THRESHOLD,),
            )
        rows = cursor.fetchall()
    return [{"code": row[0], "count": row[1]} for row in rows]


def public_stats() -> Dict[str, int]:
    regions = public_regions()
    return {"totalSignals": sum(region["count"] for region in regions), "countriesRepresented": len(regions), "displayThreshold": DISPLAY_THRESHOLD}