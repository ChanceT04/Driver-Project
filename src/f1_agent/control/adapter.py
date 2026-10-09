"""T9 boundary: imports and construction never connect to game inputs.

Backend implementation requires T9 assignment; trials require explicit user
authorization to send controls to the game.
"""
from f1_agent.training.interfaces import Action


class GameController:
    def connect(self) -> None:
        raise NotImplementedError("T9: game-input backend has not been implemented")

    def apply(self, action: Action, *, observation_time_ns: int) -> None:
        raise NotImplementedError("T9: implement supervised controls and timeout")

    def stop(self) -> None:
        raise NotImplementedError("T9: implement neutral controls and immediate stop")

    def close(self) -> None:
        raise NotImplementedError("T9: implement safe controller release")
