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

**Backend (any host with a persistent disk — Render/Fly/Railway/VPS).** Vercel cannot run this service: it needs a long-running process and a writable filesystem. The `render.yaml` at the repo root is one such option — a free web service that runs `backend/server.py`:
- `HOLDER_MAP_HOST=0.0.0.0` so the host's proxy can reach it.
- `HOLDER_MAP_DATABASE` points at a persistent disk, so counts survive restarts and deploys.
- The host injects `PORT` automatically; the process reads it.
- Expose one public URL, then set Vercel's `HOLDER_MAP_API_URL` to it.

**Frontend (Vercel).** `vercel.json` builds a `dist/` bundle (html + css + js) and injects the deployed API URL into `index.html` from the project environment variable `HOLDER_MAP_API_URL` (Vercel → Project → Settings → Environment Variables). Until that variable is set, `apiBase` stays `""` and the site serves clearly-labelled prototype data.

## Public API

- `GET /api/map` returns only regions at or above the display threshold.
- `GET /api/stats` returns aggregate totals only.

The SQLite database is created at `backend/storage/holdermap.sqlite` and is ignored by Git. It contains receipt identifiers for deduplication and must never be made public.
