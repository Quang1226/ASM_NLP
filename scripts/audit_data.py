"""Produce a reproducible first-pass Bitext data audit."""

from __future__ import annotations

import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from intent_support.data.bitext import REQUIRED_COLUMNS, SHA256, normalize_instruction, read_rows

PLACEHOLDER_RE = re.compile(r"\{\{([^{}]+)\}\}")
INVOICE_NUMBER_RE = re.compile(r"#\d+")


def main() -> None:
    rows = read_rows()
    intents = Counter(row["intent"] for row in rows)
    categories = Counter(row["category"] for row in rows)
    flags = Counter(row["flags"] for row in rows)
    missing = {column: sum(not row[column].strip() for row in rows) for column in REQUIRED_COLUMNS}
    normalized: dict[str, set[str]] = defaultdict(set)
    category_per_intent: dict[str, set[str]] = defaultdict(set)
    placeholders: Counter[str] = Counter()
    invoice_numbers: dict[str, Counter[str]] = {"check_invoice": Counter(), "get_invoice": Counter()}
    lengths = []
    for row in rows:
        normalized[normalize_instruction(row["instruction"])].add(row["intent"])
        category_per_intent[row["intent"]].add(row["category"])
        placeholders.update(PLACEHOLDER_RE.findall(row["instruction"]))
        if row["intent"] in invoice_numbers:
            invoice_numbers[row["intent"]].update(INVOICE_NUMBER_RE.findall(row["instruction"]))
        lengths.append(len(row["instruction"].split()))

    report = {
        "source_sha256": SHA256,
        "row_count": len(rows),
        "columns": list(REQUIRED_COLUMNS),
        "intent_count": len(intents),
        "intents": dict(sorted(intents.items())),
        "category_count": len(categories),
        "categories": dict(sorted(categories.items())),
        "missing": missing,
        "unique_normalized_instructions": len(normalized),
        "duplicate_rows_after_normalization": len(rows) - len(normalized),
        "conflicting_intent_groups": sum(len(labels) > 1 for labels in normalized.values()),
        "category_conflicts_by_intent": {
            intent: sorted(values) for intent, values in category_per_intent.items() if len(values) > 1
        },
        "placeholder_occurrences": dict(sorted(placeholders.items())),
        "invoice_number_occurrences": {label: dict(sorted(counts.items())) for label, counts in invoice_numbers.items()},
        "distinct_flag_values": len(flags),
        "top_flag_values": dict(flags.most_common(15)),
        "example_samples": [
            {"instruction": row["instruction"], "intent": row["intent"]}
            for row in (rows[0], rows[len(rows) // 2], rows[-1])
        ],
        "word_count": {
            "min": min(lengths),
            "median": statistics.median(lengths),
            "mean": round(statistics.mean(lengths), 2),
            "max": max(lengths),
        },
        "limitations": [
            "This audit detects matches after Unicode/case/punctuation/whitespace normalization; it does not yet prove that generated paraphrase templates are isolated across splits.",
            "The dataset is hybrid synthetic, so performance on it does not establish production reliability.",
        ],
    }
    output = ROOT / "reports"
    output.mkdir(exist_ok=True)
    (output / "data_audit.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Bitext data audit",
        "",
        f"- Rows: **{len(rows):,}**",
        f"- Intents: **{len(intents)}**; categories: **{len(categories)}**",
        f"- Unique normalized instructions: **{len(normalized):,}**",
        f"- Duplicate rows after normalization: **{len(rows) - len(normalized):,}**",
        f"- Conflicting intent groups: **{report['conflicting_intent_groups']}**",
        f"- Missing values: **{missing}**",
        "",
        "## Intent counts",
        "",
        "| Intent | Rows |",
        "| --- | ---: |",
        *(f"| {label} | {count} |" for label, count in sorted(intents.items())),
        "",
        "## Category counts",
        "",
        "| Category | Rows |",
        "| --- | ---: |",
        *(f"| {label} | {count} |" for label, count in sorted(categories.items())),
        "",
        "## Example customer requests",
        "",
        *(
            f"- `{sample['intent']}`: {sample['instruction']}"
            for sample in report["example_samples"]
        ),
        "",
        "## Caveat",
        "",
        *[f"- {item}" for item in report["limitations"]],
        "",
    ]
    split_path = output / "split_report.json"
    similarity_path = output / "split_similarity.json"
    if split_path.exists():
        split = json.loads(split_path.read_text(encoding="utf-8"))
        if split.get("source_sha256") == SHA256:
            cancel = {name: split["intent_counts"][name]["cancel_order"] for name in ("train", "validation", "test")}
            pre_cancel = split["group_stats_by_intent"]["cancel_order"]
            cancel_unique = pre_cancel["train"] + pre_cancel["validation"] + pre_cancel["test"]
            lines.extend([
                "## Post-split summary",
                "",
                f"- Deduplicated instructions before splitting: **{split['unique_rows']:,}**; removed from raw data: **{split['removed_duplicate_rows']:,}**.",
                f"- Final split: train **{split['counts']['train']:,}**, validation **{split['counts']['validation']:,}**, test **{split['counts']['test']:,}**.",
                f"- `cancel_order`: **{intents['cancel_order']:,}** raw rows -> **{cancel_unique:,}** unique normalized instructions -> **{sum(cancel.values()):,}** retained rows (train {cancel['train']}, validation {cancel['validation']}, test {cancel['test']}). This class is much smaller than most others after deduplication.",
                f"- Invoice examples reuse only **{len(set(invoice_numbers['check_invoice']) | set(invoice_numbers['get_invoice']))}** literal numbers: {', '.join(sorted(set(invoice_numbers['check_invoice']) | set(invoice_numbers['get_invoice'])))}. This is a synthetic-template limitation.",
            ])
            if "cross_split_near_duplicates_excluded" in split:
                lines.append(f"- Additional near-duplicate holdout rows excluded: **{sum(split['cross_split_near_duplicates_excluded'].values()):,}**; details in `split_report.json`.")
            if similarity_path.exists():
                similarity = json.loads(similarity_path.read_text(encoding="utf-8"))
                lines.append("- Residual cross-split matches at the reported similarity threshold: " + ", ".join(f"{name} {result['near_matches']}" for name, result in similarity["comparisons"].items()) + ".")
            lines.extend(["", "The split and similarity analysis remain separate from model selection; the test set has not been used for training or tuning.", ""])
    (output / "data_audit.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Audited {len(rows):,} rows; {len(intents)} intents; {len(categories)} categories")
    print(f"Wrote {output / 'data_audit.md'} and data_audit.json")


if __name__ == "__main__":
    main()
