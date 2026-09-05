# Privacy promise

ZEC Holder Map is deliberately a coarse, opt-in community visualization.

- We collect a country or continent code only. We do not ask for a city, GPS location, identity, public address, or account.
- The public map shows aggregate counts only. A country is withheld until it reaches the configured minimum display threshold.
- The web application will not use behavioural analytics, advertising pixels, wallet connection SDKs, or third-party map tiles.
- The public API will never return raw memos, transaction IDs, note identifiers, or individual submission timestamps.
- The receipt listener will deduplicate privately and retain only the minimum operational records needed for correctness.

## Important limit

A shielded transaction with a memo is a privacy-preserving receipt, not a zero-knowledge proof of hold. Transaction timing is observable on-chain. Do not submit a Holder Map signal if the act or timing of participation itself would be sensitive for you.
