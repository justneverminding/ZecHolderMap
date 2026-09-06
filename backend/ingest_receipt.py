#!/usr/bin/env python3
"""Private command that records a decrypted Holder Map memo.

Run it locally on the machine that owns the mailbox wallet. The wallet decrypts
the shielded memo; this command only ingests the already-decrypted country code.
No spending key, viewing key, or address ever leaves that wallet.
"""
import argparse
import sys

from database import record_receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a decrypted Holder Map testnet receipt.")
    parser.add_argument("--receipt-id", required=True,
                        help="Private, stable deduplication identifier, e.g. <txid>:<output_index> from the wallet")
    parser.add_argument("--memo", required=True, help="Decrypted memo, for example HOLDERMAP:NG")
    args = parser.parse_args()
    try:
        inserted = record_receipt(args.receipt_id, args.memo)
    except ValueError as error:
        print(f"Rejected: {error}", file=sys.stderr)
        return 2
    print("Recorded" if inserted else "Ignored duplicate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
