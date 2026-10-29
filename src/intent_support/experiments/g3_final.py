"""Evaluate the frozen G3 bundle exactly once on held-out test and challenge final."""

from __future__ import annotations

import csv
import json
import platform
import statistics
import time
from collections import defaultdict
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix

from intent_support.data.bitext import sha256_file
from intent_support.experiments.g2 import scores
from intent_support.experiments.g3_embedding import embeddings, frozen_split_manifest, load_encoder
from intent_support.experiments.g3_policy import action, challenge_rows, nearest_similarity


def _test_rows(root: Path, manifest: dict) -> list[dict]:
    path = root / "data/processed/test.csv"
    if sha256_file(path) != manifest["output_sha256"]["test"]:
        raise ValueError("Frozen test split hash mismatch")
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["sample_id", "instruction", "intent"]:
            raise ValueError("Unexpected test columns")
        rows = list(reader)
    if len(rows) != manifest["counts"]["test"]:
        raise ValueError("Test count mismatch")
    return rows


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _latency(encoder, model, bank, texts: list[str], policy: dict) -> dict:
    durations = []
    # Full single-message path, excluding model load and including encoding,
    # classifier, nearest-neighbor check, and policy decision.
    for text in texts[:5]:
        vec = encoder.encode([text], normalize_embeddings=True, show_progress_bar=False)
        probs = model.predict_proba(vec)[0]
        sim = nearest_similarity(vec, bank)[0]
        action(model.classes_[probs.argmax()], float(probs.max()), float(sim), text,
               policy["scope_similarity_threshold"], policy["clarify_probability_threshold"])
    for text in texts[:50]:
        start = time.perf_counter()
        vec = encoder.encode([text], normalize_embeddings=True, show_progress_bar=False)
        probs = model.predict_proba(vec)[0]
        sim = nearest_similarity(vec, bank)[0]
        action(model.classes_[probs.argmax()], float(probs.max()), float(sim), text,
               policy["scope_similarity_threshold"], policy["clarify_probability_threshold"])
        durations.append((time.perf_counter() - start) * 1000)
    return {"device": "cpu", "batch_size": 1, "warmup_queries": 5, "measured_queries": len(durations),
            "included": "encoder + classifier + full-train cosine search + decision (not model load)",
            "median_ms": round(statistics.median(durations), 3),
            "p95_ms": round(float(np.percentile(durations, 95)), 3),
            "min_ms": round(min(durations), 3), "max_ms": round(max(durations), 3)}


def run(root: Path) -> dict:
    report_dir = root / "reports/g3"
    final_path = report_dir / "final_evaluation.json"
    if final_path.exists():
        raise FileExistsError("Final evaluation already exists; held-out sets may not be reused for tuning")
    freeze_path = report_dir / "frozen_bundle.json"
    if not freeze_path.exists():
        raise FileNotFoundError("Freeze model and thresholds before reading test or challenge final")
    freeze_sha = sha256_file(freeze_path)
    bundle = json.loads(freeze_path.read_text(encoding="utf-8"))
    split = frozen_split_manifest(root)
    if bundle["split_hashes"] != split["output_sha256"] or bundle["selected_experiment"] != "E5":
        raise ValueError("Frozen bundle does not match G1 or selected experiment")
    challenge, challenge_manifest = challenge_rows(root, "final")
    if bundle["challenge_sha256"] != challenge_manifest["sha256"]:
        raise ValueError("Frozen challenge version changed")
    test = _test_rows(root, split)
    model_path = root / bundle["classifier"]["model_file"]
    bank_path = root / bundle["train_embedding"]["file"]
    if sha256_file(model_path) != bundle["classifier"]["model_sha256"] or sha256_file(bank_path) != bundle["train_embedding"]["file_sha256"]:
        raise ValueError("Frozen classifier or training embedding changed")
    started = time.perf_counter()
    encoder = load_encoder()
    model = joblib.load(model_path)
    bank = np.load(bank_path, allow_pickle=False)
    load_seconds = time.perf_counter() - started
    test_x, test_meta = embeddings(root, encoder, "test", [r["instruction"] for r in test], split["output_sha256"]["test"])
    final_x, final_meta = embeddings(root, encoder, "challenge_final", [r["utterance"] for r in challenge], challenge_manifest["sha256"])
    test_pred = model.predict(test_x).tolist()
    test_true = [r["intent"] for r in test]
    labels = model.classes_.tolist()
    test_scores = scores(test_true, test_pred)
    per_class = classification_report(test_true, test_pred, labels=labels, output_dict=True, zero_division=0)
    cm = confusion_matrix(test_true, test_pred, labels=labels)
    test_predictions = [{"sample_id": row["sample_id"], "instruction": row["instruction"],
                         "true_intent": row["intent"], "predicted_intent": pred}
                        for row, pred in zip(test, test_pred)]
    _write_csv(report_dir / "E5_test_predictions.csv", test_predictions)
    with (report_dir / "E5_test_confusion.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["true\\predicted", *labels])
        writer.writerows([[label, *values] for label, values in zip(labels, cm)])
    (report_dir / "E5_test_per_class.json").write_text(json.dumps(per_class, indent=2) + "\n", encoding="utf-8")
    final_probs = model.predict_proba(final_x)
    final_intents = model.classes_[final_probs.argmax(axis=1)].tolist()
    final_conf = final_probs.max(axis=1)
    final_nearest = nearest_similarity(final_x, bank)
    policy = bundle["policy"]
    final_predictions = [
        {"id": row["id"], "scenario": row["scenario"], "utterance": row["utterance"],
         "expected_intent": row["expected_intent"], "predicted_intent": intent,
         "confidence": round(float(conf), 6), "nearest_train_cosine": round(float(sim), 6),
         "expected_action": row["expected_action"],
         "predicted_action": action(intent, float(conf), float(sim), row["utterance"],
                                    policy["scope_similarity_threshold"], policy["clarify_probability_threshold"])}
        for row, intent, conf, sim in zip(challenge, final_intents, final_conf, final_nearest)
    ]
    _write_csv(report_dir / "challenge_final_predictions.csv", final_predictions)
    final_inscope = [r for r in final_predictions if r["expected_intent"]]
    final_action = {name: {"correct": sum(r["expected_action"] == name and r["predicted_action"] == name for r in final_predictions),
                           "total": sum(r["expected_action"] == name for r in final_predictions)}
                    for name in sorted({r["expected_action"] for r in final_predictions})}
    # Latency uses already-public validation text, not challenge final.
    with (root / "data/processed/validation.csv").open("r", encoding="utf-8", newline="") as stream:
        validation_texts = [r["instruction"] for r in csv.DictReader(stream)][:50]
    latency = _latency(encoder, model, bank, validation_texts, policy)
    errors = defaultdict(list)
    for row in test_predictions:
        if row["true_intent"] != row["predicted_intent"]:
            errors[(row["true_intent"], row["predicted_intent"])].append(row["instruction"])
    ranked = sorted(errors.items(), key=lambda x: (-len(x[1]), x[0]))
    report = {
        "frozen_bundle_file": "reports/g3/frozen_bundle.json", "frozen_bundle_sha256": freeze_sha,
        "test": {"count": len(test), **test_scores, "error_count": sum(len(x) for x in errors.values()),
                 "embedding": test_meta},
        "challenge_final": {"count": len(challenge), "inscope_count": len(final_inscope),
                            "inscope_intent_correct": sum(r["expected_intent"] == r["predicted_intent"] for r in final_inscope),
                            "action_correct": sum(r["expected_action"] == r["predicted_action"] for r in final_predictions),
                            "by_action": final_action, "embedding": final_meta},
        "latency": {"model_load_seconds": round(load_seconds, 3), **latency},
        "artifact_sizes_bytes": {"classifier": model_path.stat().st_size, "train_embedding": bank_path.stat().st_size},
        "platform": {"system": platform.system(), "machine": platform.machine(), "processor": platform.processor(),
                     "python": platform.python_version()},
        "test_evaluations": 1, "challenge_final_evaluations": 1,
    }
    final_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = ["# G3 final evaluation and model decision", "",
             f"Frozen bundle SHA-256: `{freeze_sha}`. Test and challenge final were evaluated after threshold selection; neither was used for model selection.", "",
             "## Validation comparison", "", "| Model | Macro-F1 | Accuracy |", "| --- | ---: | ---: |",
             *[f"| {r['experiment']} | {r['validation_macro_f1']:.6f} | {r['validation_accuracy']:.6f} |" for r in bundle["comparison"]], "",
             "E5 (frozen all-MiniLM-L6-v2 embeddings + Logistic Regression) was selected by validation macro-F1. E3 and E4 remain useful light baselines. High scores on synthetic Bitext do not establish real-world accuracy.", "",
             "## Held-out Bitext test", "",
             f"{len(test)} cases; accuracy {test_scores['accuracy']:.6f}; macro precision {test_scores['macro_precision']:.6f}; macro recall {test_scores['macro_recall']:.6f}; macro-F1 {test_scores['macro_f1']:.6f}.", "",
             "## Challenge final", "",
             f"In-scope intent: {report['challenge_final']['inscope_intent_correct']}/{len(final_inscope)}; action: {report['challenge_final']['action_correct']}/{len(challenge)}.", "",
             "| Expected action | Correct | Total |", "| --- | ---: | ---: |",
             *[f"| {name} | {item['correct']} | {item['total']} |" for name, item in final_action.items()], "",
             "The 22-case final partition is too small to estimate deployment OOS performance. The probability score is a classifier output, not a calibrated probability of being in scope. The cosine boundary was tuned on only four OOS examples; broader human-reviewed OOS coverage is needed before relying on automatic scope decisions.", "",
             "## Latency on this machine", "",
             f"CPU, single message, 5 warm-up queries and {latency['measured_queries']} measured validation queries. Model load {load_seconds:.3f} s; median {latency['median_ms']:.3f} ms; p95 {latency['p95_ms']:.3f} ms. Timed path: {latency['included']}.", "",
             "## Frequent test confusions", "", "| True | Predicted | Count |", "| --- | --- | ---: |",
             *[f"| {a} | {b} | {len(texts)} |" for (a, b), texts in ranked[:10]], "",
             "## Representative mistakes", "",
             *[f"- `{a}` → `{b}`: {texts[0]}" for (a, b), texts in ranked[:8]], "",
             "## Decision for G4", "",
             "Use frozen E5 for intent prediction. Keep safe `clarify`/`scope_boundary` fallbacks visible in the demo and do not claim these thresholds generalize beyond the small challenge set. KB answers are separate from Bitext responses. The encoder revision is pinned in the bundle and downloaded separately during setup.", ""]
    (report_dir / "final_report.md").write_text("\n".join(lines), encoding="utf-8")
    return report
