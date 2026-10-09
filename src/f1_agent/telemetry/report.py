"""Offline capture-quality report; no game access or controller input."""

from __future__ import annotations

from collections import Counter, defaultdict
import math
from pathlib import Path
import statistics

from .capture import read_capture
from .decoder import CarTelemetry, DecodeError, Lap, Motion, decode


def _interval_summary(values_ns: list[int]) -> dict[str, float] | None:
    if not values_ns:
        return None
    intervals_ms = sorted(value / 1_000_000 for value in values_ns)
    p95_index = max(0, (95 * len(intervals_ms) + 99) // 100 - 1)
    mean_ms = statistics.mean(intervals_ms)
    return {
        "mean_ms": mean_ms,
        "median_ms": statistics.median(intervals_ms),
        "p95_ms": intervals_ms[p95_index],
        "max_ms": intervals_ms[-1],
        "approx_hz": 1000 / mean_ms if mean_ms > 0 else 0.0,
    }


def _add_range(ranges: dict[str, list[float]], name: str, value: float) -> None:
    if not math.isfinite(value):
        return
    bounds = ranges.get(name)
    if bounds is None:
        ranges[name] = [value, value]
    else:
        bounds[0] = min(bounds[0], value)
        bounds[1] = max(bounds[1], value)


def summarize(path: Path) -> dict[str, object]:
    """Summarize recorded datagrams without claiming network loss or latency."""
    counts: Counter[int] = Counter()
    malformed = 0
    unsupported = 0
    total = 0
    format_counts: Counter[int] = Counter()
    session_uids: set[int] = set()
    packet_lengths: dict[int, Counter[int]] = defaultdict(Counter)
    packet_versions: dict[int, Counter[int]] = defaultdict(Counter)
    player_indices: dict[int, Counter[int]] = defaultdict(Counter)
    arrival_intervals: dict[int, list[int]] = defaultdict(list)
    previous_arrival: dict[tuple[int, int], int] = {}
    previous_frame: dict[tuple[int, int], int] = {}
    frame_gaps: Counter[int] = Counter()
    frame_regressions: Counter[int] = Counter()
    action_frame_ids = (0, 2, 6)
    frame_keys_by_packet: dict[int, set[tuple[int, int]]] = {packet_id: set() for packet_id in action_frame_ids}
    arrival_by_packet_frame: dict[int, dict[tuple[int, int], int]] = {
        packet_id: {} for packet_id in action_frame_ids
    }
    positions: list[tuple[float, float, float]] = []
    previous_position_by_session: dict[int, tuple[float, float, float]] = {}
    first_position_by_session: dict[int, tuple[float, float, float]] = {}
    last_position_by_session: dict[int, tuple[float, float, float]] = {}
    player_value_ranges: dict[str, list[float]] = {}
    observed_gears: set[int] = set()
    invalid_lap_samples = 0
    lap_number_transitions = 0
    completed_lap_invalid_count = 0
    completed_lap_times_ms: list[int] = []
    last_lap_state: dict[tuple[int, int], tuple[int, bool]] = {}
    motion_samples = 0
    nonfinite_motion_samples = 0
    estimated_path_length_m = 0.0
    largest_position_step_m = 0.0
    position_steps_over_100m = 0
    lap_samples = 0
    telemetry_samples = 0

    for arrival_ns, datagram in read_capture(path):
        total += 1
        try:
            packet = decode(datagram)
        except DecodeError:
            malformed += 1
            if len(datagram) >= 2:
                format_counts[int.from_bytes(datagram[:2], "little")] += 1
            continue
        header = packet.header
        session_uids.add(header.session_uid)
        counts[header.packet_id] += 1
        format_counts[header.packet_format] += 1
        packet_lengths[header.packet_id][len(datagram)] += 1
        packet_versions[header.packet_id][header.packet_version] += 1
        player_indices[header.packet_id][header.player_car_index] += 1
        if not packet.supported:
            unsupported += 1
        stream_key = (header.session_uid, header.packet_id)
        if header.packet_id in frame_keys_by_packet:
            frame_key = (header.session_uid, header.overall_frame_id)
            frame_keys_by_packet[header.packet_id].add(frame_key)
            arrival_by_packet_frame[header.packet_id][frame_key] = arrival_ns
        last_arrival = previous_arrival.get(stream_key)
        if last_arrival is not None and arrival_ns >= last_arrival:
            arrival_intervals[header.packet_id].append(arrival_ns - last_arrival)
        previous_arrival[stream_key] = arrival_ns
        prior = previous_frame.get(stream_key)
        if prior is not None:
            delta = header.overall_frame_id - prior
            if delta > 1:
                frame_gaps[header.packet_id] += delta - 1
            elif delta < 0:
                frame_regressions[header.packet_id] += 1
        previous_frame[stream_key] = header.overall_frame_id
        player = packet.player
        if isinstance(player, Motion):
            motion_samples += 1
            if all(math.isfinite(value) for value in player.position_m):
                positions.append(player.position_m)
                prior_position = previous_position_by_session.get(header.session_uid)
                if prior_position is not None:
                    step = math.dist(prior_position, player.position_m)
                    estimated_path_length_m += step
                    largest_position_step_m = max(largest_position_step_m, step)
                    if step > 100.0:
                        position_steps_over_100m += 1
                else:
                    first_position_by_session[header.session_uid] = player.position_m
                previous_position_by_session[header.session_uid] = player.position_m
                last_position_by_session[header.session_uid] = player.position_m
            else:
                nonfinite_motion_samples += 1
        elif isinstance(player, Lap):
            lap_samples += 1
            invalid_lap_samples += int(player.current_lap_invalid)
            _add_range(player_value_ranges, "lap_distance_m", player.lap_distance_m)
            _add_range(player_value_ranges, "current_lap_time_ms", player.current_lap_time_ms)
            lap_key = (header.session_uid, header.player_car_index)
            prior_lap = last_lap_state.get(lap_key)
            if prior_lap is not None and player.current_lap_number != prior_lap[0]:
                lap_number_transitions += 1
                completed_lap_invalid_count += int(prior_lap[1])
                if player.last_lap_time_ms > 0:
                    completed_lap_times_ms.append(player.last_lap_time_ms)
            last_lap_state[lap_key] = (player.current_lap_number, player.current_lap_invalid)
        elif isinstance(player, CarTelemetry):
            telemetry_samples += 1
            _add_range(player_value_ranges, "speed_kph", player.speed_kph)
            _add_range(player_value_ranges, "throttle", player.throttle)
            _add_range(player_value_ranges, "steer", player.steer)
            _add_range(player_value_ranges, "brake", player.brake)
            observed_gears.add(player.gear)

    interval_report: dict[str, dict[str, float] | None] = {}
    for packet_id in sorted(counts):
        interval_report[str(packet_id)] = _interval_summary(arrival_intervals[packet_id])
    position_bounds: dict[str, list[float]] | None = None
    if positions:
        position_bounds = {
            axis: [min(point[i] for point in positions), max(point[i] for point in positions)]
            for i, axis in enumerate(("x", "y", "z"))
        }
    common_frames = set.intersection(*(frame_keys_by_packet[packet_id] for packet_id in action_frame_ids))
    all_action_frames = set.union(*(frame_keys_by_packet[packet_id] for packet_id in action_frame_ids))
    aligned_arrival_skews_ns = [
        max(arrival_by_packet_frame[packet_id][key] for packet_id in action_frame_ids)
        - min(arrival_by_packet_frame[packet_id][key] for packet_id in action_frame_ids)
        for key in common_frames
    ]
    return {
        "total_datagrams": total,
        "session_count": len(session_uids),
        "packet_counts": {str(key): value for key, value in sorted(counts.items())},
        "packet_format_counts": {str(key): value for key, value in sorted(format_counts.items())},
        "packet_lengths_by_id": {
            str(packet_id): {str(length): count for length, count in sorted(lengths.items())}
            for packet_id, lengths in sorted(packet_lengths.items())
        },
        "packet_versions_by_id": {
            str(packet_id): {str(version): count for version, count in sorted(versions.items())}
            for packet_id, versions in sorted(packet_versions.items())
        },
        "player_car_indices_by_id": {
            str(packet_id): {str(index): count for index, count in sorted(indices.items())}
            for packet_id, indices in sorted(player_indices.items())
        },
        "malformed_datagrams": malformed,
        "unsupported_datagrams": unsupported,
        "arrival_intervals_by_packet_id": interval_report,
        "frame_id_jumps_by_packet_id": {str(key): value for key, value in sorted(frame_gaps.items())},
        "frame_id_regressions_by_packet_id": {str(key): value for key, value in sorted(frame_regressions.items())},
        "action_frame_alignment": {
            "packet_ids": list(action_frame_ids),
            "unique_frames_by_packet_id": {
                str(packet_id): len(frame_keys_by_packet[packet_id]) for packet_id in action_frame_ids
            },
            "frames_present_in_all_three": len(common_frames),
            "union_of_frames": len(all_action_frames),
            "arrival_skew_ms_for_shared_frames": _interval_summary(aligned_arrival_skews_ns),
        },
        "player_motion_samples": motion_samples,
        "nonfinite_motion_samples": nonfinite_motion_samples,
        "player_telemetry_samples": telemetry_samples,
        "player_lap_samples": lap_samples,
        "invalid_lap_samples": invalid_lap_samples,
        "lap_number_transitions": lap_number_transitions,
        "completed_lap_invalid_at_transition": completed_lap_invalid_count,
        "completed_lap_times_ms": completed_lap_times_ms,
        "player_position_bounds_m": position_bounds,
        "estimated_position_path_length_m": estimated_path_length_m,
        "largest_position_sample_step_m": largest_position_step_m,
        "position_steps_over_100m": position_steps_over_100m,
        "first_to_last_position_distance_m": sum(
            math.dist(first_position_by_session[uid], last_position_by_session[uid])
            for uid in first_position_by_session
        ),
        "player_value_ranges": player_value_ranges,
        "observed_gears": sorted(observed_gears),
        "interpretation": "Frame jumps are discontinuities in sampled IDs, not proof of UDP loss. Arrival intervals are not end-to-end control latency.",
    }
