"""Offline command routing. Feature implementations belong to their tickets.

Help and config inspection work now. Unfinished operations report their owner
and exit unsuccessfully; they never create a pretend run or checkpoint.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .training.config import load_config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline F1 driving experiments")
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("check-config", help="check shared configuration structure")
    check.add_argument("--config", type=Path, required=True)

    for name, description in (
        ("preview-tracks", "T3: inspect generated track layouts"),
        ("simulate", "T4A: watch or record a diagnostic driving episode"),
        ("train", "T6: train a policy across generated tracks"),
        ("evaluate", "T5/T6: evaluate a baseline or frozen policy"),
    ):
        command = commands.add_parser(name, help=description)
        command.add_argument("--config", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True, help="new output directory")
        if name == "simulate":
            command.add_argument("--route", type=Path, help="T1 JSON route; otherwise use generator")
        if name == "evaluate":
            command.add_argument("--checkpoint", type=Path, help="omit to compare diagnostic baselines")
            command.add_argument("--split", choices=("validation", "test"), default="validation")

    replay = commands.add_parser("replay", help="T4A: render a saved driving episode")
    replay.add_argument("episode", type=Path)
    replay.add_argument("--output", type=Path, required=True, help="new render file")

    args = parser.parse_args(argv)
    try:
        if args.command == "replay":
            from .environment.render import replay_episode
            replay_episode(args.episode, args.output)
        else:
            config = load_config(args.config)
            if args.command == "check-config":
                print("Shared configuration structure is valid. Physics, observation and algorithm "
                      "settings still require validation by their implementing tickets.")
            elif args.command == "preview-tracks":
                from .track.procedural import preview_tracks
                preview_tracks(config, args.output)
            elif args.command == "simulate":
                from .environment.demo import simulate
                simulate(config, args.output, route_path=args.route)
            elif args.command == "train":
                from .training.sim_train import train
                train(config, args.output)
            elif args.command == "evaluate":
                from .evaluation.metrics import evaluate
                evaluate(config, args.output, checkpoint=args.checkpoint, split=args.split)
    except (NotImplementedError, OSError, ValueError) as error:
        parser.exit(1, f"f1-sim: {error}\n")
    return 0
