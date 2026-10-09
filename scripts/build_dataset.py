"""Export valid completed laps as aligned offline model examples."""

import argparse
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from f1_agent.training.dataset import DatasetError, build_valid_lap_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path, help="raw telemetry JSONL capture")
    parser.add_argument("output", type=Path, help="new processed JSONL dataset file")
    args = parser.parse_args()
    try:
        result = build_valid_lap_dataset(args.capture, args.output)
    except (DatasetError, OSError, ValueError) as error:
        parser.exit(1, f"build-dataset: {error}\n")
    print(f"Exported {result['samples']} samples from {result['valid_laps']} valid laps to {result['output']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
