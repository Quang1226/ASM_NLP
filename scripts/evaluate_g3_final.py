"""Run the one-time held-out evaluation after G3 bundle freeze."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from intent_support.experiments.g3_final import run

if __name__ == "__main__":
    result = run(ROOT)
    print("G3 test macro-F1", result["test"]["macro_f1"])
    print("G3 challenge final action", result["challenge_final"]["action_correct"], "/", result["challenge_final"]["count"])
