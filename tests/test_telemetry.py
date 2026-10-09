"""Contract tests using literal sizes and offsets from EA's 2026 structures."""

from __future__ import annotations

import base64
import json
from pathlib import Path
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
PROJECT_ROOT = Path(__file__).resolve().parents[1]

from f1_agent.telemetry.capture import CaptureError, read_capture, record_udp
from f1_agent.telemetry.decoder import CarTelemetry, DecodeError, Lap, Motion, decode
from f1_agent.telemetry.report import summarize


def header(packet_id: int, *, player_index: int = 7, frame: int = 100, packet_format: int = 2026) -> bytes:
    # Independently place each field at the spec's absolute header offsets.
    result = bytearray(29)
    result[0:2] = packet_format.to_bytes(2, "little")
    result[2:7] = bytes((26, 1, 0, 1, packet_id))
    result[7:15] = (12345).to_bytes(8, "little")
    result[15:19] = struct.pack("<f", 12.5)
    result[19:23] = frame.to_bytes(4, "little")
    result[23:27] = frame.to_bytes(4, "little")
    result[27:29] = bytes((player_index, 255))
    return bytes(result)


def packet(packet_id: int, length: int, *, player_index: int = 7, frame: int = 100) -> bytearray:
    data = bytearray(length)
    data[:29] = header(packet_id, player_index=player_index, frame=frame)
    return data


class DecoderTests(unittest.TestCase):
    def test_header_and_unsupported_packet(self) -> None:
        result = decode(header(16) + b"unparsed payload")
        self.assertEqual(result.header.packet_format, 2026)
        self.assertEqual(result.header.game_year, 26)
        self.assertEqual(result.header.session_uid, 12345)
        self.assertEqual(result.header.session_time_s, 12.5)
        self.assertEqual(result.header.frame_id, 100)
        self.assertEqual(result.header.player_car_index, 7)
        self.assertEqual(result.header.secondary_player_car_index, 255)
        self.assertFalse(result.supported)
        self.assertIsNone(result.player)

    def test_motion_nonzero_and_last_car(self) -> None:
        for index in (7, 23):
            with self.subTest(index=index):
                data = packet(0, 1325, player_index=index)
                offset = 29 + index * 54
                struct.pack_into("<6f", data, offset, 101.25, -2.5, 303.5, 21.0, 0.0, -4.0)
                struct.pack_into("<3f", data, offset + 42, 1.25, -0.5, 0.75)
                result = decode(bytes(data)).player
                self.assertIsInstance(result, Motion)
                self.assertEqual(result.position_m, (101.25, -2.5, 303.5))
                self.assertEqual(result.velocity_mps, (21.0, 0.0, -4.0))
                self.assertEqual((result.yaw_rad, result.pitch_rad, result.roll_rad), (1.25, -0.5, 0.75))

    def test_lap_offsets_and_negative_distance(self) -> None:
        data = packet(2, 1399)
        offset = 29 + 7 * 57
        struct.pack_into("<II", data, offset, 90001, 12345)
        struct.pack_into("<ff", data, offset + 20, -8.5, 470.25)
        data[offset + 33] = 4
        data[offset + 36] = 2
        data[offset + 37] = 1
        result = decode(bytes(data)).player
        self.assertIsInstance(result, Lap)
        self.assertEqual((result.last_lap_time_ms, result.current_lap_time_ms), (90001, 12345))
        self.assertEqual((result.lap_distance_m, result.total_distance_m), (-8.5, 470.25))
        self.assertEqual((result.current_lap_number, result.sector, result.current_lap_invalid), (4, 2, True))

    def test_car_telemetry_offsets_and_signed_gear(self) -> None:
        data = packet(6, 1448)
        offset = 29 + 7 * 59
        struct.pack_into("<Hfff", data, offset, 287, 0.625, -0.25, 0.125)
        data[offset + 14] = 40  # clutch separates brake from signed gear
        struct.pack_into("<bH", data, offset + 15, -1, 12000)
        result = decode(bytes(data)).player
        self.assertIsInstance(result, CarTelemetry)
        self.assertEqual(result.speed_kph, 287)
        self.assertEqual((result.throttle, result.steer, result.brake), (0.625, -0.25, 0.125))
        self.assertEqual((result.gear, result.engine_rpm), (-1, 12000))

    def test_exact_lengths_index_and_format(self) -> None:
        for packet_id, length in ((0, 1325), (2, 1399), (6, 1448)):
            with self.subTest(packet_id=packet_id):
                self.assertTrue(decode(bytes(packet(packet_id, length))).supported)
                for bad in (length - 1, length + 1):
                    data = packet(packet_id, bad)
                    with self.assertRaises(DecodeError):
                        decode(bytes(data))
                with self.assertRaises(DecodeError):
                    decode(bytes(packet(packet_id, length, player_index=24)))
        with self.assertRaises(DecodeError):
            decode(header(0)[:28])
        with self.assertRaises(DecodeError):
            decode(header(16, packet_format=2025))


class CaptureTests(unittest.TestCase):
    def test_udp_capture_preserves_arbitrary_datagrams_and_shuts_down(self) -> None:
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT) as temporary:
            output = Path(temporary) / "raw.jsonl"
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as reserve:
                reserve.bind(("127.0.0.1", 0))
                port = reserve.getsockname()[1]
            result: list[int] = []
            errors: list[Exception] = []

            def run() -> None:
                try:
                    result.append(record_udp(output, port=port, duration_s=2, max_packets=2))
                except Exception as error:
                    errors.append(error)

            worker = threading.Thread(target=run, daemon=True)
            worker.start()
            deadline = time.monotonic() + 3
            while not output.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(output.exists(), "recorder did not bind and create capture")
            payloads = (b"\x00\xff\x10", b"not an EA packet")
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender:
                for payload in payloads:
                    sender.sendto(payload, ("127.0.0.1", port))
                    time.sleep(0.05)
            worker.join(timeout=3)
            self.assertFalse(worker.is_alive(), "recorder did not stop at max_packets")
            self.assertEqual(errors, [])
            self.assertEqual(result, [2])
            lines = output.read_text(encoding="utf-8").splitlines()
            metadata = json.loads(lines[0])
            self.assertEqual((metadata["schema_version"], metadata["bind_port"]), (1, port))
            recovered = list(read_capture(output))
            self.assertEqual([data for _, data in recovered], list(payloads))
            self.assertGreaterEqual(recovered[1][0], recovered[0][0])
            with self.assertRaises(FileExistsError):
                record_udp(output, port=0, max_packets=1)

    def test_duration_stops_without_packets(self) -> None:
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT) as temporary:
            output = Path(temporary) / "empty.jsonl"
            self.assertEqual(record_udp(output, port=0, duration_s=0.05), 0)
            self.assertEqual(list(read_capture(output)), [])

    def test_malformed_capture_record_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT) as temporary:
            output = Path(temporary) / "invalid.jsonl"
            output.write_text('{"type":"capture","schema_version":1}\n'
                              '{"type":"packet","arrival_monotonic_ns":3,"data_b64":"@@"}\n', encoding="utf-8")
            with self.assertRaises(CaptureError):
                list(read_capture(output))


class ReportTests(unittest.TestCase):
    def test_report_counts_supported_unsupported_and_frame_jumps(self) -> None:
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT) as temporary:
            output = Path(temporary) / "sample.jsonl"
            motion1 = packet(0, 1325, frame=100)
            motion2 = packet(0, 1325, frame=103)
            struct.pack_into("<3f", motion1, 29 + 7 * 54, 1.0, 2.0, 3.0)
            struct.pack_into("<3f", motion2, 29 + 7 * 54, 4.0, 5.0, 6.0)
            values = (bytes(motion1), bytes(motion2), header(16), b"bad")
            with output.open("w", encoding="utf-8") as stream:
                stream.write(json.dumps({"type": "capture", "schema_version": 1}) + "\n")
                for i, value in enumerate(values):
                    stream.write(json.dumps({"type": "packet", "arrival_monotonic_ns": i * 10_000_000,
                                             "data_b64": base64.b64encode(value).decode("ascii")}) + "\n")
            report = summarize(output)
            self.assertEqual(report["total_datagrams"], 4)
            self.assertEqual(report["packet_counts"], {"0": 2, "16": 1})
            self.assertEqual(report["packet_lengths_by_id"]["0"], {"1325": 2})
            self.assertEqual(report["packet_versions_by_id"]["0"], {"1": 2})
            self.assertEqual(report["player_car_indices_by_id"]["0"], {"7": 2})
            self.assertEqual(report["malformed_datagrams"], 1)
            self.assertEqual(report["unsupported_datagrams"], 1)
            self.assertEqual(report["frame_id_jumps_by_packet_id"], {"0": 2})
            self.assertEqual(report["arrival_intervals_by_packet_id"]["0"]["median_ms"], 10.0)
            self.assertEqual(report["arrival_intervals_by_packet_id"]["0"]["approx_hz"], 100.0)
            self.assertEqual(report["player_position_bounds_m"], {
                "x": [1.0, 4.0], "y": [2.0, 5.0], "z": [3.0, 6.0],
            })

    def test_cli_capture_and_report(self) -> None:
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT) as temporary:
            output = Path(temporary) / "cli.jsonl"
            script = PROJECT_ROOT / "scripts" / "telemetry.py"
            captured = subprocess.run(
                [sys.executable, str(script), "capture", str(output), "--port", "0", "--duration", "0.05"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(captured.returncode, 0, captured.stderr)
            self.assertTrue(output.exists())
            reported = subprocess.run(
                [sys.executable, str(script), "report", str(output)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(reported.returncode, 0, reported.stderr)
            self.assertEqual(json.loads(reported.stdout)["total_datagrams"], 0)

    def test_report_counts_lap_number_transitions_separately_from_invalid_samples(self) -> None:
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT) as temporary:
            output = Path(temporary) / "laps.jsonl"
            laps = []
            for frame, lap_number, invalid, last_lap_ms in (
                (10, 1, 1, 0), (11, 1, 1, 0), (12, 2, 0, 105000),
            ):
                data = packet(2, 1399, frame=frame)
                offset = 29 + 7 * 57
                struct.pack_into("<I", data, offset, last_lap_ms)
                data[offset + 33] = lap_number
                data[offset + 37] = invalid
                laps.append(bytes(data))
            with output.open("w", encoding="utf-8") as stream:
                stream.write(json.dumps({"type": "capture", "schema_version": 1}) + "\n")
                for i, value in enumerate(laps):
                    stream.write(json.dumps({"type": "packet", "arrival_monotonic_ns": i * 16_000_000,
                                             "data_b64": base64.b64encode(value).decode("ascii")}) + "\n")
            report = summarize(output)
            self.assertEqual(report["invalid_lap_samples"], 2)
            self.assertEqual(report["lap_number_transitions"], 1)
            self.assertEqual(report["completed_lap_invalid_at_transition"], 1)
            self.assertEqual(report["completed_lap_times_ms"], [105000])

    def test_report_measures_observation_action_packet_alignment(self) -> None:
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT) as temporary:
            output = Path(temporary) / "aligned.jsonl"
            values = (bytes(packet(0, 1325, frame=200)),
                      bytes(packet(2, 1399, frame=200)),
                      bytes(packet(6, 1448, frame=200)))
            with output.open("w", encoding="utf-8") as stream:
                stream.write(json.dumps({"type": "capture", "schema_version": 1}) + "\n")
                for i, value in enumerate(values):
                    stream.write(json.dumps({"type": "packet", "arrival_monotonic_ns": i * 1_000_000,
                                             "data_b64": base64.b64encode(value).decode("ascii")}) + "\n")
            alignment = summarize(output)["action_frame_alignment"]
            self.assertEqual(alignment["frames_present_in_all_three"], 1)
            self.assertEqual(alignment["union_of_frames"], 1)
            self.assertEqual(alignment["arrival_skew_ms_for_shared_frames"]["max_ms"], 2.0)


if __name__ == "__main__":
    unittest.main()
