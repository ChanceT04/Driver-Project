"""T7: Session fields decoded against the documented 2026 packet format."""
from dataclasses import dataclass


@dataclass(frozen=True)
class SessionMetadata:
    track_id: int
    track_length_m: int
    session_type: int


def decode_session(datagram: bytes) -> SessionMetadata:
    raise NotImplementedError("T7: implement and verify Session packet decoding")
