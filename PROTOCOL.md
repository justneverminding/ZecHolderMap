# Holder Map receipt protocol

## Planned memo grammar

```
HOLDERMAP:<REGION>
```

`<REGION>` is initially an uppercase ISO 3166-1 alpha-2 country code, for example:

```
HOLDERMAP:NG
HOLDERMAP:BR
HOLDERMAP:JP
```

The service accepts only shielded receipts to the published, dedicated Holder Map mailbox. Free-text memos and malformed codes are rejected. One accepted transaction receives one signal; a transaction/note is processed at most once.

## Public data

Only aggregated region totals above the minimum display threshold are published. The mailbox address, wallet material, raw receipts, and deduplication identifiers are not part of the public API.
