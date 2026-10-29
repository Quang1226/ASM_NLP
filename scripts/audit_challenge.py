"""Check label coverage, review state, and source similarity of challenge cases."""

from __future__ import annotations

import csv
import difflib
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from intent_support.data.bitext import read_rows

CHALLENGE_PATH = ROOT / "data" / "challenge" / "challenge_draft.csv"
MANIFEST_PATH = ROOT / "data" / "challenge" / "challenge_manifest.json"


def main() -> None:
    raw = read_rows()
    with CHALLENGE_PATH.open("r", encoding="utf-8", newline="") as stream:
        cases = list(csv.DictReader(stream))
    by_intent: dict[str, list[str]] = defaultdict(list)
    for row in raw:
        by_intent[row["intent"]].append(row["instruction"])
    expected_labels = set(by_intent)
    covered = {row["expected_intent"] for row in cases if row["expected_intent"]}
    if covered != expected_labels:
        raise ValueError(f"Challenge label mismatch: missing {sorted(expected_labels - covered)}, extra {sorted(covered - expected_labels)}")
    if len({row["id"] for row in cases}) != len(cases):
        raise ValueError("Duplicate challenge case ID")
    challenge_sha256 = hashlib.sha256(CHALLENGE_PATH.read_bytes()).hexdigest()
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if manifest.get("sha256") != challenge_sha256:
            raise ValueError("Approved challenge set differs from locked manifest; create a new reviewed version")
        if any(row["review_status"] != "approved" for row in cases):
            raise ValueError("Locked challenge set contains an unapproved row")

    scores = []
    for case in cases:
        label = case["expected_intent"]
        if not label:
            continue
        text = case["utterance"].casefold()
        score, nearest = max(
            (
                difflib.SequenceMatcher(None, text, source.casefold()).ratio(),
                source,
            )
            for source in by_intent[label]
        )
        scores.append({"id": case["id"], "intent": label, "maximum_same_intent_similarity": round(score, 4), "closest_source": nearest})

    report = {
        "cases": len(cases),
        "challenge_sha256": challenge_sha256,
        "locked_manifest": str(MANIFEST_PATH.relative_to(ROOT)) if MANIFEST_PATH.exists() else None,
        "partition_counts": dict(Counter(row["partition"] for row in cases)),
        "scenario_counts": dict(Counter(row["scenario"] for row in cases)),
        "review_status_counts": dict(Counter(row["review_status"] for row in cases)),
        "intent_coverage": len(covered),
        "similarity_method": "maximum difflib.SequenceMatcher ratio against all Bitext instructions with the same intent",
        "in_scope_cases_at_or_above_0_75": [item for item in scores if item["maximum_same_intent_similarity"] >= 0.75],
        "scores": scores,
        "caveat": "A low string-similarity score does not prove that an utterance is semantically independent of the synthetic dataset. Student review remains required.",
    }
    path = ROOT / "reports" / "challenge_audit.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Audited {len(cases)} cases; {len(covered)} intent labels covered; {len(report['in_scope_cases_at_or_above_0_75'])} in-scope cases >= 0.75 source similarity")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
