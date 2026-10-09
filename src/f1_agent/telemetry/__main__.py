"""Command-line entry point for read-only telemetry tools."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .capture import CaptureError, record_udp
from .report import summarize


def main() -> int:
    parser = argparse.ArgumentParser(description="F1 25 2026-format telemetry tools")
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("capture", help="record exact UDP datagrams")
    capture.add_argument("output", type=Path, help="new JSONL file to create")
    capture.add_argument("--host", default="127.0.0.1")
    capture.add_argument("--port", type=int, default=20777)
    capture.add_argument("--duration", type=float, default=None, help="seconds; Ctrl+C also stops")
    capture.add_argument("--max-packets", type=int, default=None)
    report = commands.add_parser("report", help="summarize a saved capture")
    report.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "capture":
            count = record_udp(args.output, host=args.host, port=args.port,
                               duration_s=args.duration, max_packets=args.max_packets)
            print(f"Recorded {count} datagrams to {args.output}")
        else:
            print(json.dumps(summarize(args.input), indent=2))
    except (OSError, ValueError, CaptureError) as error:
        parser.exit(1, f"telemetry: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
