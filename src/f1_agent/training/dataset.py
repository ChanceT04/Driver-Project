"""Build aligned observation/action examples from valid completed laps."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import BinaryIO

from f1_agent.telemetry.capture import read_capture
from f1_agent.telemetry.decoder import CarTelemetry, DecodeError, Lap, Motion, decode


class DatasetError(ValueError):
    """The capture cannot safely produce the requested training examples."""


@dataclass
class _Frame:
    motion: Motion | None = None
    lap: Lap | None = None
    controls: CarTelemetry | None = None
    arrival_ns: dict[int, int] | None = None

    def set_packet(self, packet_id: int, payload: Motion | Lap | CarTelemetry, arrival_ns: int) -> None:
        if self.arrival_ns is None:
            self.arrival_ns = {}
        self.arrival_ns[packet_id] = arrival_ns
        if packet_id == 0:
            assert isinstance(payload, Motion)
            self.motion = payload
        elif packet_id == 2:
            assert isinstance(payload, Lap)
            self.lap = payload
        else:
            assert isinstance(payload, CarTelemetry)
            self.controls = payload

    @property
    def complete(self) -> bool:
        return self.motion is not None and self.lap is not None and self.controls is not None


@dataclass(frozen=True)
class _LapSegment:
    session_uid: int
    lap_number: int
    lap_time_ms: int
    frames: list[tuple[tuple[int, int], _Frame]]


def _write_jsonl_line(stream: BinaryIO, value: dict[str, object]) -> None:
    stream.write((json.dumps(value, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8"))


def _collect_frames(capture_path: Path) -> tuple[dict[tuple[int, int], _Frame], int]:
    frames: dict[tuple[int, int], _Frame] = {}
    malformed = 0
    for arrival_ns, datagram in read_capture(capture_path):
        try:
            decoded = decode(datagram)
        except DecodeError as error:
            malformed += 1
            raise DatasetError(f"cannot build examples: malformed datagram ({error})") from error
        if decoded.header.packet_id not in (0, 2, 6) or decoded.player is None:
            continue
        key = (decoded.header.session_uid, decoded.header.overall_frame_id)
        frame = frames.setdefault(key, _Frame())
        packet_id = decoded.header.packet_id
        if frame.arrival_ns is not None and packet_id in frame.arrival_ns:
            raise DatasetError(f"duplicate packet ID {packet_id} for frame {key[1]}")
        frame.set_packet(packet_id, decoded.player, arrival_ns)
    return frames, malformed


def _valid_completed_laps(frames: dict[tuple[int, int], _Frame]) -> tuple[list[_LapSegment], int, int]:
    sessions: dict[int, list[tuple[tuple[int, int], _Frame]]] = {}
    for key, frame in frames.items():
        if frame.lap is not None:
            sessions.setdefault(key[0], []).append((key, frame))

    segments: list[_LapSegment] = []
    incomplete_frame_count = sum(not frame.complete for frame in frames.values())
    invalid_completed_laps = 0
    for session_uid, records in sessions.items():
        records.sort(key=lambda record: record[0][1])
        groups: list[list[tuple[tuple[int, int], _Frame]]] = []
        for record in records:
            lap = record[1].lap
            assert lap is not None
            if not groups or groups[-1][-1][1].lap.current_lap_number != lap.current_lap_number:
                groups.append([])
            groups[-1].append(record)

        for group_index, group in enumerate(groups[:-1]):
            prior_lap = group[-1][1].lap
            transition_lap = groups[group_index + 1][0][1].lap
            assert prior_lap is not None and transition_lap is not None
            if transition_lap.last_lap_time_ms <= 0:
                continue
            start_index = 0
            if group_index == 0 and group[0][1].lap is not None and group[0][1].lap.lap_distance_m < 0:
                start_index = next((index for index, (_, frame) in enumerate(group)
                                    if frame.lap is not None and frame.lap.lap_distance_m >= 0), len(group))
            lap_frames = group[start_index:]
            if not lap_frames or any(not frame.complete for _, frame in lap_frames):
                continue
            if prior_lap.current_lap_invalid or any(frame.lap is None or frame.lap.current_lap_invalid
                                                    for _, frame in lap_frames):
                invalid_completed_laps += 1
                continue
            segments.append(_LapSegment(session_uid, prior_lap.current_lap_number,
                                        transition_lap.last_lap_time_ms, lap_frames))
    return segments, incomplete_frame_count, invalid_completed_laps


def build_valid_lap_dataset(capture_path: Path, output_path: Path) -> dict[str, object]:
    """Export one JSONL sample per aligned frame of each valid completed lap.

    A lap beginning in the middle of a capture is excluded up to the first
    non-negative lap-distance sample. No partial or invalid laps are exported.
    Output is created exclusively so existing processed data is never replaced.
    """
    frames, malformed = _collect_frames(capture_path)
    if malformed:
        raise DatasetError(f"capture contained {malformed} malformed datagrams")
    segments, incomplete_frames, invalid_laps = _valid_completed_laps(frames)
    if not segments:
        raise DatasetError("capture contains no complete, aligned, valid lap to export")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    exported = 0
    with output_path.open("xb") as stream:
        _write_jsonl_line(stream, {
            "type": "dataset",
            "schema_version": 1,
            "source_capture": capture_path.name,
            "selection": "valid_completed_laps",
            "observation_fields": {
                "position_m": "world x,y,z in metres",
                "velocity_mps": "world vx,vy,vz in metres per second",
                "yaw_pitch_roll_rad": "radians",
                "lap_distance_m": "metres from start/finish line",
                "speed_kph": "kilometres per hour",
            },
            "action_fields": {"steer": "-1 left to +1 right", "throttle": "0 to 1", "brake": "0 to 1"},
            "completed_laps": [
                {"lap_number": segment.lap_number, "lap_time_ms": segment.lap_time_ms,
                 "sample_count": len(segment.frames)}
                for segment in segments
            ],
            "incomplete_aligned_frames_excluded": incomplete_frames,
            "invalid_completed_laps_excluded": invalid_laps,
        })
        for segment in segments:
            for (session_uid, frame_id), frame in segment.frames:
                assert frame.motion is not None and frame.lap is not None
                assert frame.controls is not None and frame.arrival_ns is not None
                values = (*frame.motion.position_m, *frame.motion.velocity_mps,
                          frame.motion.yaw_rad, frame.motion.pitch_rad, frame.motion.roll_rad,
                          frame.lap.lap_distance_m, frame.controls.throttle,
                          frame.controls.steer, frame.controls.brake)
                if not all(math.isfinite(value) for value in values):
                    raise DatasetError(f"non-finite model value at overall frame {frame_id}")
                _write_jsonl_line(stream, {
                    "type": "sample",
                    "overall_frame_id": frame_id,
                    "arrival_monotonic_ns": {
                        str(packet_id): timestamp for packet_id, timestamp in sorted(frame.arrival_ns.items())
                    },
                    "observation": {
                        "position_m": frame.motion.position_m,
                        "velocity_mps": frame.motion.velocity_mps,
                        "yaw_pitch_roll_rad": [frame.motion.yaw_rad, frame.motion.pitch_rad, frame.motion.roll_rad],
                        "lap_distance_m": frame.lap.lap_distance_m,
                        "speed_kph": frame.controls.speed_kph,
                    },
                    "action": {
                        "steer": frame.controls.steer,
                        "throttle": frame.controls.throttle,
                        "brake": frame.controls.brake,
                    },
                })
                exported += 1
    return {"output": str(output_path), "samples": exported, "valid_laps": len(segments),
            "incomplete_frames_excluded": incomplete_frames, "invalid_laps_excluded": invalid_laps}
