"""Train E5 on the frozen train split; select C on validation only."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from intent_support.experiments.g3_embedding import run

if __name__ == "__main__":
    result = run(ROOT)
    print("E5 selected", result["selected"])
