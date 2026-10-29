"""Freeze G3 model selection and decision thresholds before final evaluation."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from intent_support.experiments.g3_policy import run

if __name__ == "__main__":
    report = run(ROOT)
    print(report["selected_experiment"], report["policy"])
