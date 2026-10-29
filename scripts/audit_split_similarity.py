"""Exhaustively measure residual near-matches across data splits."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from intent_support.data.similarity import SimilarityIndex
from split_data import SIMILARITY_THRESHOLD


def read_split(name: str) -> list[dict[str, str]]:
    with (ROOT / "data" / "processed" / f"{name}.csv").open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def compare(source: list[dict[str, str]], target: list[dict[str, str]]) -> dict:
    """Every same-intent pair that can reach the threshold is checked."""
    index = SimilarityIndex(source, SIMILARITY_THRESHOLD)
    matches = 0
    examples = []
    for row in target:
        other = index.first_match(row)
        if other is not None:
            matches += 1
            if len(examples) < 5:
                examples.append({"target": row["instruction"], "source": other, "intent": row["intent"]})
    return {"target_rows": len(target), "near_matches": matches, "rate": round(matches / len(target), 4), "examples": examples}


def main() -> None:
    splits = {name: read_split(name) for name in ("train", "validation", "test")}
    results = {
        "method": f"exhaustive same-intent pair search, difflib.SequenceMatcher ratio >= {SIMILARITY_THRESHOLD}; length and quick-ratio bounds prune only impossible pairs",
        "caveat": "Exact for this string-similarity definition, but semantic paraphrases below the threshold or with different wording can still cross splits.",
        "comparisons": {
            "train_to_validation": compare(splits["train"], splits["validation"]),
            "train_to_test": compare(splits["train"], splits["test"]),
            "validation_to_test": compare(splits["validation"], splits["test"]),
        },
    }
    path = ROOT / "reports" / "split_similarity.json"
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, result in results["comparisons"].items():
        print(f"{name}: {result['near_matches']}/{result['target_rows']} ({result['rate']:.2%})")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
