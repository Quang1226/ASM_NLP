"""Select a conservative G3 decision policy using validation and challenge tuning."""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np

from intent_support.data.bitext import sha256_file
from intent_support.experiments.g3_embedding import embeddings, frozen_split_manifest, load_encoder

HUMAN_REQUEST = re.compile(r"\b(real (?:support )?person|human (?:agent|support)|live agent|talk to (?:a )?person)\b", re.I)


def challenge_rows(root: Path, partition: str) -> tuple[list[dict], dict]:
    if partition not in {"tuning", "final"}:
        raise ValueError("Unknown challenge partition")
    manifest = json.loads((root / "data/challenge/challenge_manifest.json").read_text(encoding="utf-8"))
    path = root / manifest["file"]
    if manifest.get("status") != "approved_by_student_before_model_training" or sha256_file(path) != manifest["sha256"]:
        raise ValueError("Challenge set is not the approved frozen version")
    with path.open("r", encoding="utf-8", newline="") as stream:
        rows = [row for row in csv.DictReader(stream) if row["partition"] == partition]
    if len(rows) != manifest["partitions"][partition] or any(row["review_status"] != "approved" for row in rows):
        raise ValueError("Challenge partition count or review status changed")
    return rows, manifest


def nearest_similarity(queries: np.ndarray, bank: np.ndarray, batch_size: int = 128) -> np.ndarray:
    if queries.ndim != 2 or bank.ndim != 2 or queries.shape[1] != bank.shape[1]:
        raise ValueError("Embedding bank has incompatible shape")
    results = []
    for start in range(0, len(queries), batch_size):
        similarities = queries[start:start + batch_size] @ bank.T
        results.append(similarities.max(axis=1))
    return np.concatenate(results).astype(np.float32)


def action(predicted_intent: str, confidence: float, nearest: float, utterance: str,
           scope_threshold: float, clarify_threshold: float) -> str:
    if nearest < scope_threshold:
        return "scope_boundary"
    if HUMAN_REQUEST.search(utterance) or (predicted_intent == "contact_human_agent" and confidence >= clarify_threshold):
        return "handoff"
    if confidence < clarify_threshold:
        return "clarify"
    return "guide"


def _midpoints(values: np.ndarray) -> list[float]:
    ordered = sorted({float(x) for x in values})
    return [0.0, *[(a + b) / 2 for a, b in zip(ordered, ordered[1:])], 1.0]


def select_thresholds(rows: list[dict], intents: list[str], confidence: np.ndarray,
                      nearest: np.ndarray, validation_confidence: np.ndarray,
                      validation_nearest: np.ndarray) -> tuple[dict, list[dict]]:
    # OOS false acceptance is costlier than a safe refusal. The validation guard
    # limits false refusals on known in-scope examples; tiny challenge tuning is
    # explicitly not treated as a general OOS benchmark.
    scope_options = _midpoints(nearest)
    clarify_options = _midpoints(confidence)
    best = None
    for scope in scope_options:
        if float(np.mean(validation_nearest < scope)) > 0.01:
            continue
        for clarify in clarify_options:
            if float(np.mean(validation_confidence < clarify)) > 0.03:
                continue
            predictions = [action(intent, float(conf), float(sim), row["utterance"], scope, clarify)
                           for row, intent, conf, sim in zip(rows, intents, confidence, nearest)]
            loss = 0
            for row, predicted in zip(rows, predictions):
                expected = row["expected_action"]
                if expected == predicted:
                    continue
                loss += 5 if expected == "scope_boundary" else 3 if expected == "clarify" else 2 if expected == "handoff" else 1
            # Prefer higher guide coverage in a tie; avoid arbitrary extreme boundaries.
            key = (loss, sum(p != "guide" and r["expected_action"] == "guide" for p, r in zip(predictions, rows)), scope, clarify)
            if best is None or key < best[0]:
                best = (key, scope, clarify, predictions)
    if best is None:
        raise ValueError("No threshold pair meets validation false-refusal guards")
    _, scope, clarify, predictions = best
    result_rows = [
        {"id": row["id"], "scenario": row["scenario"], "expected_intent": row["expected_intent"],
         "predicted_intent": intent, "confidence": round(float(conf), 6),
         "nearest_train_cosine": round(float(sim), 6), "expected_action": row["expected_action"],
         "predicted_action": predicted}
        for row, intent, conf, sim, predicted in zip(rows, intents, confidence, nearest, predictions)
    ]
    policy = {
        "scope_similarity_threshold": round(scope, 6),
        "clarify_probability_threshold": round(clarify, 6),
        "score_type": "E5 LogisticRegression.predict_proba; not calibrated as OOS probability",
        "nearest_score_type": "maximum cosine similarity against frozen normalized training embeddings",
        "human_request_rule": HUMAN_REQUEST.pattern,
        "selection_rule": "Minimize weighted challenge-tuning action loss (scope miss=5, ambiguity miss=3, handoff miss=2, guide rejection=1), subject to <=1% validation scope refusals and <=3% validation confidence clarifications; ties favor guide coverage.",
        "validation_scope_refusal_rate": round(float(np.mean(validation_nearest < scope)), 6),
        "validation_confidence_clarification_rate": round(float(np.mean(validation_confidence < clarify)), 6),
        "tuning_action_accuracy": round(sum(x["expected_action"] == x["predicted_action"] for x in result_rows) / len(result_rows), 6),
        "tuning_by_action": {name: {"correct": sum(x["expected_action"] == name and x["predicted_action"] == name for x in result_rows),
                                    "total": sum(x["expected_action"] == name for x in result_rows)}
                             for name in sorted({x["expected_action"] for x in result_rows})},
    }
    return policy, result_rows


def run(root: Path) -> dict:
    report_dir = root / "reports/g3"
    freeze_path = report_dir / "frozen_bundle.json"
    if freeze_path.exists():
        raise FileExistsError("G3 bundle already frozen; do not retune after final evaluation")
    split = frozen_split_manifest(root)
    challenge, challenge_manifest = challenge_rows(root, "tuning")
    e5 = json.loads((report_dir / "e5_validation.json").read_text(encoding="utf-8"))
    if e5["split_hashes"] != split["output_sha256"]:
        raise ValueError("E5 validation used another split")
    model_path = root / e5["selected"]["model_file"]
    if sha256_file(model_path) != e5["selected"]["model_sha256"]:
        raise ValueError("E5 classifier hash changed")
    bank_path = root / e5["train_embedding"]["file"]
    val_path = root / e5["validation_embedding"]["file"]
    for path, meta in ((bank_path, e5["train_embedding"]), (val_path, e5["validation_embedding"])):
        if sha256_file(path) != meta["file_sha256"]:
            raise ValueError(f"Embedding cache hash changed: {path}")
    bank = np.load(bank_path, allow_pickle=False)
    validation_x = np.load(val_path, allow_pickle=False)
    encoder = load_encoder()
    tuning_x, tuning_meta = embeddings(root, encoder, "challenge_tuning", [r["utterance"] for r in challenge], challenge_manifest["sha256"])
    model = joblib.load(model_path)
    tuning_proba = model.predict_proba(tuning_x)
    validation_proba = model.predict_proba(validation_x)
    tuning_intents = model.classes_[tuning_proba.argmax(axis=1)].tolist()
    tuning_conf = tuning_proba.max(axis=1)
    val_conf = validation_proba.max(axis=1)
    tuning_nearest = nearest_similarity(tuning_x, bank)
    validation_nearest = nearest_similarity(validation_x, bank)
    policy, tuning_rows = select_thresholds(challenge, tuning_intents, tuning_conf, tuning_nearest, val_conf, validation_nearest)
    with (report_dir / "challenge_tuning_predictions.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(tuning_rows[0]))
        writer.writeheader()
        writer.writerows(tuning_rows)
    inscope = [x for x in tuning_rows if x["expected_intent"]]
    g2 = json.loads((root / "reports/g2/best_by_experiment.json").read_text(encoding="utf-8"))
    comparison = [{"experiment": x["experiment"], "validation_macro_f1": x["macro_f1"],
                   "validation_accuracy": x["accuracy"]} for x in g2 if x["experiment"] in {"E3", "E4"}]
    comparison.append({"experiment": "E5", "validation_macro_f1": e5["selected"]["macro_f1"],
                       "validation_accuracy": e5["selected"]["accuracy"],
                       "tuning_inscope_intent_accuracy": round(sum(x["expected_intent"] == x["predicted_intent"] for x in inscope) / len(inscope), 6)})
    freeze = {
        "bundle_version": "g3-v1-2026-10-28", "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "selected_experiment": "E5", "selection_basis": "highest validation macro-F1 among E3, E4, E5; policy selected on challenge tuning under validation refusal guards",
        "comparison": comparison, "classifier": e5["selected"],
        "encoder": {"model_id": e5["model_id"], "revision": e5["model_revision"],
                    "license": e5["license"], "input": e5["encoder_input"], "device": "cpu"},
        "train_embedding": e5["train_embedding"], "validation_embedding": e5["validation_embedding"],
        "challenge_tuning_embedding": tuning_meta,
        "split_version": split["split_version"], "split_hashes": split["output_sha256"],
        "challenge_version": challenge_manifest["challenge_version"], "challenge_sha256": challenge_manifest["sha256"],
        "policy": policy, "tuning_inscope_intent_count": len(inscope),
        "tuning_inscope_intent_correct": sum(x["expected_intent"] == x["predicted_intent"] for x in inscope),
        "test_used": False, "challenge_final_used": False,
    }
    report_dir.mkdir(parents=True, exist_ok=True)
    freeze_path.write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
    return freeze
