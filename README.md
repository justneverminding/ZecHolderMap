# ZecHolderMap

ZEC Holder Map is an opt-in, anonymous community pulse for the Zcash ecosystem. Holders send a small shielded transaction with a memo that tags only a country or continent. The public map displays aggregate, coarse signals — never identities, wallet addresses, or exact locations.

## Prototype

This repository currently contains the static map prototype. It intentionally uses local mock aggregate data and no analytics, wallet connections, or third-party map tiles.

Open `index.html` in a browser, or serve this directory with any static-file server.

## Memo format (planned)

`HOLDERMAP:NG` for a country using an ISO 3166-1 alpha-2 code. Only shielded receipts will be processed by the later ingestion service.

Read [PRIVACY.md](PRIVACY.md) and [PROTOCOL.md](PROTOCOL.md) before implementing the listener.
