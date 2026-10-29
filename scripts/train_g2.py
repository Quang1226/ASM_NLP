"""Run G2 E1-E4 and one-factor preprocessing ablations on validation only."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from intent_support.experiments.g2 import run


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--c-grid", nargs="+", type=float, default=[0.1, 1.0, 10.0])
    args = parser.parse_args()
    outcome = run(ROOT, tuple(args.c_grid))
    selected = outcome["selected"]
    print(f"G2 selected {selected['experiment']} at C={selected['C']:g}, validation macro-F1={selected['macro_f1']:.4f}")


if __name__ == "__main__":
    main()
