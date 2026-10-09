"""Lossless, decoder-independent UDP capture in line-oriented JSON."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import socket
import time
from typing import BinaryIO, Iterator


SCHEMA_VERSION = 1
MAX_DATAGRAM_BYTES = 65535


class CaptureError(ValueError):
    """A saved capture is malformed or uses an unsupported schema."""


def _write_record(stream: BinaryIO, record: dict[str, object]) -> None:
    stream.write((json.dumps(record, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8"))


def record_udp(
    output: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 20777,
    duration_s: float | None = None,
    max_packets: int | None = None,
) -> int:
    """Bind locally and save complete datagrams until interrupted or limited.

    The JSONL file begins with capture metadata, followed by packet records.
    No packet parsing or validation occurs on the receive path.
    """
    if not 0 <= port <= 65535:
        raise ValueError("port must be between 0 and 65535")
    if duration_s is not None and duration_s <= 0:
        raise ValueError("duration_s must be positive")
    if max_packets is not None and max_packets <= 0:
        raise ValueError("max_packets must be positive")
    output.parent.mkdir(parents=True, exist_ok=True)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
        udp.bind((host, port))
        udp.settimeout(0.2)
        bound_port = udp.getsockname()[1]
        started_ns = time.monotonic_ns()
        started_utc = datetime.now(timezone.utc).isoformat()
        count = 0
        with output.open("xb") as stream:
            _write_record(stream, {
                "type": "capture", "schema_version": SCHEMA_VERSION,
                "started_utc": started_utc, "monotonic_origin_ns": started_ns,
                "bind_host": host, "bind_port": bound_port,
                "configured_udp_format": 2026,
            })
            try:
                while True:
                    if duration_s is not None and time.monotonic_ns() - started_ns >= duration_s * 1e9:
                        break
                    try:
                        datagram, address = udp.recvfrom(MAX_DATAGRAM_BYTES)
                    except socket.timeout:
                        continue
                    arrival_ns = time.monotonic_ns()
                    _write_record(stream, {
                        "type": "packet", "arrival_monotonic_ns": arrival_ns,
                        "source_ip": address[0], "source_port": address[1],
                        "data_b64": base64.b64encode(datagram).decode("ascii"),
                    })
                    count += 1
                    if max_packets is not None and count >= max_packets:
                        break
            except KeyboardInterrupt:
                pass
            finally:
                stream.flush()
    return count


def read_capture(path: Path) -> Iterator[tuple[int, bytes]]:
    """Replay a schema-1 capture as (monotonic arrival ns, original bytes)."""
    with path.open("rb") as stream:
        try:
            metadata = json.loads(next(stream))
        except (StopIteration, ValueError) as error:
            raise CaptureError("capture metadata is missing or invalid") from error
        if not isinstance(metadata, dict) or metadata.get("type") != "capture" or metadata.get("schema_version") != SCHEMA_VERSION:
            raise CaptureError("unsupported capture metadata")
        for line_number, raw in enumerate(stream, start=2):
            try:
                record = json.loads(raw)
                if not isinstance(record, dict) or record.get("type") != "packet":
                    raise ValueError("expected packet record")
                arrival = record["arrival_monotonic_ns"]
                if type(arrival) is not int or arrival < 0:
                    raise ValueError("invalid arrival timestamp")
                data = base64.b64decode(record["data_b64"], validate=True)
            except (KeyError, TypeError, ValueError) as error:
                raise CaptureError(f"invalid capture record on line {line_number}") from error
            yield arrival, data
