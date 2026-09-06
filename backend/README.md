# Holder Map testnet backend

The backend keeps three deliberately separate responsibilities:

- `ingest_receipt.py` accepts a memo and a private receipt identifier, already decrypted by the mailbox wallet.
- `database.py` validates, deduplicates, and aggregates the event in SQLite.
- `server.py` exposes aggregate-only read endpoints and can serve the static map.

It does **not** create a wallet, hold a key, connect to a Zcash node, or expose an internet-facing ingestion endpoint. Decryption happens in the wallet that owns the mailbox address — on whichever machine you run — and only the plaintext country code reaches this backend.

## Mailbox flow

1. The map publishes a shielded mailbox address (`HOLDER_MAP_CONFIG.mailboxAddress`).
2. Someone sends a `HOLDERMAP:XX` memo in a shielded transaction to it.
3. Your wallet shows the decrypted memo in its transaction list.
4. You (or your wallet script) pass the decrypted memo locally:

```bash
python3 backend/ingest_receipt.py --receipt-id <txid>:<output_index> --memo HOLDERMAP:NG
```

`<txid>:<output_index>` is the stable deduplication key. Only a valid ISO 3166-1 alpha-2 country code is accepted; anything else is rejected.

## Local test

```bash
python3 backend/ingest_receipt.py --receipt-id testnet-demo-001 --memo HOLDERMAP:NG
python3 backend/server.py
```

Open `http://127.0.0.1:4173`. The public map deliberately hides a region until it has five valid receipts. Repeat the command with five unique test receipt IDs to make a region appear.

## Tests

```bash
cd backend && python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Each test runs against a fresh temporary SQLite database; the storage directory is never touched.

## Deployment

Two independent pieces:

**Backend (Render).** `render.yaml` defines a free web service plus a free Postgres database:
- The web service runs `backend/server.py` with `HOLDER_MAP_HOST=0.0.0.0`; Render injects `PORT` automatically.
- `HOLDER_MAP_DATABASE` is wired to the `holder_map` Postgres instance via `fromDatabase` — SQLite cannot persist on a free Render service, because free services have an ephemeral filesystem and cannot attach disks.
- Postgres makes the schema compatible: `database.py` opens the same tables and queries against `postgres://` URLs (via pg8000) or local SQLite paths.

Note the free Postgres **expires 30 days after creation** (then a 14-day grace period before deletion). Upgrade it to a paid plan when that matters.

**Ingesting from your machine.** The operator runs the ingestion locally, targeting the same database URL:

```bash
HOLDER_MAP_DATABASE='postgres://...' python3 backend/ingest_receipt.py --receipt-id <txid>:<output_index> --memo HOLDERMAP:NG
```

(Install the local dependency with `pip install -r backend/requirements.txt`.) There is still no internet-facing ingestion endpoint — decrypting and calling the CLI stays on your machine.

**Frontend (Vercel).** `vercel.json` builds a `dist/` bundle (html + css + js) and injects the deployed API URL into `index.html` from the project environment variable `HOLDER_MAP_API_URL` (Vercel → Project → Settings → Environment Variables). Until that variable is set, `apiBase` stays `""` and the site serves clearly-labelled prototype data.

## Public API

- `GET /api/map` returns only regions at or above the display threshold.
- `GET /api/stats` returns aggregate totals only.

The SQLite database is created at `backend/storage/holdermap.sqlite` and is ignored by Git. It contains receipt identifiers for deduplication and must never be made public.
