"""T8: calibrated HUD and UDP to the observations used by the simulator."""
from typing import Mapping
from f1_agent.training.interfaces import Observation


class ObservationAdapter:
    def __init__(self, settings: Mapping[str, object]) -> None:
        raise NotImplementedError("T8: implement calibrated read-only observation adapter")

    def latest(self, *, now_ns: int) -> Observation:
        """Flag age, missing data and failed calibration before any policy uses it."""
        raise NotImplementedError("T8: implement timestamped live observations")
