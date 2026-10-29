"""Group-aware split with exact cross-split similarity pruning."""

from __future__ import annotations

import csv
import difflib
import hashlib
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from intent_support.data.bitext import SHA256, normalize_instruction, read_rows, sha256_file
from intent_support.data.similarity import SimilarityIndex

SEED = 42
FIELDS = ("sample_id", "instruction", "intent")
SIMILARITY_THRESHOLD = 0.90
SHINGLE_SIZE = 4
RARE_SHINGLES = 16


def unique_examples(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    seen: dict[str, dict[str, str]] = {}
    for row in rows:
        key = normalize_instruction(row["instruction"])
        if not key:
            raise ValueError("Blank normalized instruction")
        if key in seen and seen[key]["intent"] != row["intent"]:
            raise ValueError(f"Conflicting labels for {key!r}")
        seen.setdefault(key, row)
    by_intent: dict[str, list[dict[str, str]]] = defaultdict(list)
    for key, row in sorted(seen.items()):
        by_intent[row["intent"]].append(
            {
                "sample_id": hashlib.sha256(key.encode("utf-8")).hexdigest()[:16],
                "instruction": row["instruction"],
                "intent": row["intent"],
            }
        )
    return by_intent


def shingles(text: str) -> set[str]:
    normalized = re.sub(r"\s+", " ", text.casefold())
    return {
        normalized[i : i + SHINGLE_SIZE]
        for i in range(max(0, len(normalized) - SHINGLE_SIZE + 1))
        if normalized[i : i + SHINGLE_SIZE].strip()
    }


def near_duplicate_groups(examples: list[dict[str, str]]) -> list[list[dict[str, str]]]:
    """Approximate candidate search, then exact SequenceMatcher verification."""
    texts = [row["instruction"].casefold() for row in examples]
    all_shingles = [shingles(text) for text in texts]
    index: dict[str, list[int]] = defaultdict(list)
    for i, grams in enumerate(all_shingles):
        for gram in grams:
            index[gram].append(i)

    parent = list(range(len(examples)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, text in enumerate(texts):
        rare = sorted(all_shingles[i], key=lambda gram: (len(index[gram]), gram))[:RARE_SHINGLES]
        candidates = sorted({j for gram in rare for j in index[gram] if j < i})
        for j in candidates:
            other = texts[j]
            if abs(len(text) - len(other)) > max(len(text), len(other)) * 0.15:
                continue
            if difflib.SequenceMatcher(None, text, other).ratio() >= SIMILARITY_THRESHOLD:
                parent[find(i)] = find(j)

    groups: dict[int, list[dict[str, str]]] = defaultdict(list)
    for i, row in enumerate(examples):
        groups[find(i)].append(row)
    return sorted(groups.values(), key=lambda group: min(normalize_instruction(row["instruction"]) for row in group))


def make_splits(
    by_intent: dict[str, list[dict[str, str]]],
) -> tuple[dict[str, list[dict[str, str]]], dict[str, dict[str, int]]]:
    rng = random.Random(SEED)
    splits: dict[str, list[dict[str, str]]] = {"train": [], "validation": [], "test": []}
    group_stats = {}
    for label in sorted(by_intent):
        groups = near_duplicate_groups(by_intent[label])
        rng.shuffle(groups)
        groups.sort(key=len, reverse=True)
        targets = {"train": len(by_intent[label]) * 0.70, "validation": len(by_intent[label]) * 0.15, "test": len(by_intent[label]) * 0.15}
        counts = {name: 0 for name in targets}
        for group in groups:
            destination = max(targets, key=lambda name: (targets[name] - counts[name], -counts[name]))
            splits[destination].extend(group)
            counts[destination] += len(group)
        group_stats[label] = {"groups": len(groups), "largest_group": max(map(len, groups)), **counts}
    for examples in splits.values():
        examples.sort(key=lambda row: row["sample_id"])
    return splits, group_stats


def prune_cross_split_near_duplicates(
    splits: dict[str, list[dict[str, str]]],
) -> tuple[dict[str, list[dict[str, str]]], dict[str, int]]:
    """Keep the training set and remove holdout rows similar to an earlier split."""
    train_index = SimilarityIndex(splits["train"], SIMILARITY_THRESHOLD)
    validation = [row for row in splits["validation"] if train_index.first_match(row) is None]
    removed_validation = len(splits["validation"]) - len(validation)
    validation_index = SimilarityIndex(validation, SIMILARITY_THRESHOLD)
    test = []
    removed_test_train = 0
    removed_test_validation = 0
    for row in splits["test"]:
        if train_index.first_match(row) is not None:
            removed_test_train += 1
        elif validation_index.first_match(row) is not None:
            removed_test_validation += 1
        else:
            test.append(row)
    return (
        {"train": splits["train"], "validation": validation, "test": test},
        {
            "validation_similar_to_train": removed_validation,
            "test_similar_to_train": removed_test_train,
            "test_similar_to_validation": removed_test_validation,
        },
    )


def main() -> None:
    rows = read_rows()
    by_intent = unique_examples(rows)
    initial_splits, group_stats = make_splits(by_intent)
    splits, removed = prune_cross_split_near_duplicates(initial_splits)
    keys = [{normalize_instruction(row["instruction"]) for row in examples} for examples in splits.values()]
    if any(keys[i] & keys[j] for i in range(3) for j in range(i + 1, 3)):
        raise AssertionError("Normalized instruction overlap across splits")
    label_sets = [set(row["intent"] for row in examples) for examples in splits.values()]
    if not all(labels == label_sets[0] for labels in label_sets[1:]):
        raise AssertionError("Some labels are absent from a split")

    output = ROOT / "data" / "processed"
    output.mkdir(parents=True, exist_ok=True)
    for split, examples in splits.items():
        with (output / f"{split}.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(examples)

    report = {
        "split_version": "v1-strict-2026-10-28",
        "status": "frozen_before_model_training",
        "source_sha256": SHA256,
        "seed": SEED,
        "strategy": "Unicode/case/punctuation/whitespace deduplication, approximate near-duplicate grouping within each intent, then group-aware allocation toward 70/15/15",
        "near_duplicate_method": {
            "candidate_search": f"{RARE_SHINGLES} rarest character {SHINGLE_SIZE}-grams per sentence",
            "verification": "difflib.SequenceMatcher ratio",
            "threshold": SIMILARITY_THRESHOLD,
            "scope": "within intent",
        },
        "raw_rows": len(rows),
        "unique_rows": sum(map(len, by_intent.values())),
        "removed_duplicate_rows": len(rows) - sum(map(len, by_intent.values())),
        "counts": {name: len(examples) for name, examples in splits.items()},
        "output_sha256": {name: sha256_file(output / f"{name}.csv") for name in splits},
        "intent_counts": {name: dict(sorted(Counter(row["intent"] for row in examples).items())) for name, examples in splits.items()},
        "group_stats_by_intent": group_stats,
        "pre_pruning_counts": {name: len(examples) for name, examples in initial_splits.items()},
        "cross_split_near_duplicates_excluded": removed,
        "normalized_exact_overlap": 0,
        "limitation": "The final holdouts have no cross-split same-intent matches at SequenceMatcher >= 0.90, but lower-similarity paraphrases and cross-intent semantic ambiguity can remain. Large connected groups also make per-class sizes uneven.",
    }
    path = ROOT / "reports" / "split_report.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Split {report['unique_rows']:,} unique rows: {report['counts']}")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
