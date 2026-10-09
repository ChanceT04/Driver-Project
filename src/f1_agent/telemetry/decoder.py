"""Pure decoder for selected 2026 UDP packets.

Layout source: EA's 2026 Season Pack Telemetry Output Structures (1).txt.
All offsets are packed, little-endian byte offsets. Only packet IDs 0, 2, and 6
are decoded; other IDs retain their header and are reported as unsupported.
"""

from __future__ import annotations

from dataclasses import dataclass
import struct


HEADER = struct.Struct("<HBBBBBQfIIBB")
HEADER_SIZE = HEADER.size
CAR_COUNT = 24
PACKET_LENGTHS = {0: 1325, 2: 1399, 6: 1448}
CAR_STRIDES = {0: 54, 2: 57, 6: 59}


class DecodeError(ValueError):
    """A datagram cannot be interpreted as the selected 2026 UDP format."""


@dataclass(frozen=True)
class Header:
    packet_format: int
    game_year: int
    game_major_version: int
    game_minor_version: int
    packet_version: int
    packet_id: int
    session_uid: int
    session_time_s: float
    frame_id: int
    overall_frame_id: int
    player_car_index: int
    secondary_player_car_index: int


@dataclass(frozen=True)
class Motion:
    position_m: tuple[float, float, float]
    velocity_mps: tuple[float, float, float]
    yaw_rad: float
    pitch_rad: float
    roll_rad: float


@dataclass(frozen=True)
class Lap:
    last_lap_time_ms: int
    current_lap_time_ms: int
    lap_distance_m: float
    total_distance_m: float
    current_lap_number: int
    sector: int
    current_lap_invalid: bool


@dataclass(frozen=True)
class CarTelemetry:
    speed_kph: int
    throttle: float
    steer: float
    brake: float
    gear: int
    engine_rpm: int


Payload = Motion | Lap | CarTelemetry


@dataclass(frozen=True)
class DecodedPacket:
    header: Header
    player: Payload | None

    @property
    def supported(self) -> bool:
        return self.header.packet_id in PACKET_LENGTHS


def decode_header(datagram: bytes) -> Header:
    if len(datagram) < HEADER_SIZE:
        raise DecodeError(f"header requires {HEADER_SIZE} bytes, got {len(datagram)}")
    header = Header(*HEADER.unpack_from(datagram))
    if header.packet_format != 2026:
        raise DecodeError(f"expected UDP packet format 2026, got {header.packet_format}")
    return header


def decode(datagram: bytes) -> DecodedPacket:
    header = decode_header(datagram)
    packet_id = header.packet_id
    if packet_id not in PACKET_LENGTHS:
        return DecodedPacket(header, None)
    expected = PACKET_LENGTHS[packet_id]
    if len(datagram) != expected:
        raise DecodeError(f"packet {packet_id} requires {expected} bytes, got {len(datagram)}")
    if not 0 <= header.player_car_index < CAR_COUNT:
        raise DecodeError(f"invalid player car index {header.player_car_index}")

    offset = HEADER_SIZE + header.player_car_index * CAR_STRIDES[packet_id]
    if packet_id == 0:
        position_and_velocity = struct.unpack_from("<6f", datagram, offset)
        yaw, pitch, roll = struct.unpack_from("<3f", datagram, offset + 42)
        player: Payload = Motion(
            position_m=position_and_velocity[:3],
            velocity_mps=position_and_velocity[3:],
            yaw_rad=yaw, pitch_rad=pitch, roll_rad=roll,
        )
    elif packet_id == 2:
        last_ms, current_ms = struct.unpack_from("<II", datagram, offset)
        lap_distance, total_distance = struct.unpack_from("<ff", datagram, offset + 20)
        player = Lap(
            last_lap_time_ms=last_ms,
            current_lap_time_ms=current_ms,
            lap_distance_m=lap_distance,
            total_distance_m=total_distance,
            current_lap_number=datagram[offset + 33],
            sector=datagram[offset + 36],
            current_lap_invalid=bool(datagram[offset + 37]),
        )
    else:
        speed, throttle, steer, brake = struct.unpack_from("<Hfff", datagram, offset)
        gear = struct.unpack_from("<b", datagram, offset + 15)[0]
        engine_rpm = struct.unpack_from("<H", datagram, offset + 16)[0]
        player = CarTelemetry(speed, throttle, steer, brake, gear, engine_rpm)
    return DecodedPacket(header, player)
