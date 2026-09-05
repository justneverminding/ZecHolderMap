# Holder Map testnet backend

This is a local, testnet-only scaffold. It has three deliberately separate responsibilities:

- `ingest_receipt.py` accepts a memo and a private receipt identifier from a future trusted Zcash listener.
- `database.py` validates, deduplicates, and aggregates the event in SQLite.
- `server.py` exposes aggregate-only read endpoints and can serve the static map.

It does **not** create a wallet, hold a spending key, connect to a Zcash node, or expose an internet-facing ingestion endpoint. A future listener must pass already-decrypted shielded memos to the ingestion command locally.

## Local test

```bash
python3 backend/ingest_receipt.py --receipt-id testnet-demo-001 --memo HOLDERMAP:NG
python3 backend/server.py
```

Open `http://127.0.0.1:4173`. The public map deliberately hides a region until it has five valid receipts. Repeat the command with five unique test receipt IDs to make a region appear.

## Public API

- `GET /api/map` returns only regions at or above the display threshold.
- `GET /api/stats` returns aggregate totals only.

The SQLite database is created at `backend/storage/holdermap.sqlite` and is ignored by Git. It contains receipt identifiers for deduplication and must never be made public.
