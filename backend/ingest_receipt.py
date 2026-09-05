#!/usr/bin/env python3
"""Private command invoked by the future Zcash testnet memo listener."""
import argparse
import sys

from database import record_receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a decrypted Holder Map testnet receipt.")
    parser.add_argument("--receipt-id", required=True, help="Private, stable deduplication identifier from the listener")
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
