"""G2: four word-representation/classifier experiments and preprocessing ablations."""

from __future__ import annotations

import csv
import json
import platform
import time
import warnings
from collections import defaultdict
from pathlib import Path

import joblib
import nltk
import numpy
import scipy
import sklearn
from joblib import Memory
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_recall_fscore_support
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from intent_support.data.bitext import SHA256, sha256_file
from intent_support.preprocessing.text import TextPreprocessor, identity_tokens

EXPERIMENTS = {
    "E1": ("bow", "logistic_regression"),
    "E2": ("bow", "linear_svm"),
    "E3": ("tfidf", "logistic_regression"),
    "E4": ("tfidf", "linear_svm"),
}
DEFAULT_PREPROCESS = {"normalize": True, "tokenizer": "regex", "lemmatize": True}
ABLATIONS = {
    "no_normalization": {"normalize": False, "tokenizer": "regex", "lemmatize": True},
    "whitespace_tokenizer": {"normalize": True, "tokenizer": "whitespace", "lemmatize": True},
    "no_lemmatization": {"normalize": True, "tokenizer": "regex", "lemmatize": False},
}


def build_pipeline(
    representation: str,
    classifier: str,
    c: float,
    preprocess: dict | None = None,
    memory: Memory | None = None,
) -> Pipeline:
    if c <= 0:
        raise ValueError("C must be positive")
    if representation not in {"bow", "tfidf"}:
        raise ValueError(f"Unknown representation: {representation}")
    if classifier not in {"logistic_regression", "linear_svm"}:
        raise ValueError(f"Unknown classifier: {classifier}")
    vectorizer_type = CountVectorizer if representation == "bow" else TfidfVectorizer
    vectorizer = vectorizer_type(
        tokenizer=identity_tokens,
        token_pattern=None,
        lowercase=False,
        ngram_range=(1, 2),
        min_df=2,
        max_features=50000,
    )
    model = (
        LogisticRegression(C=c, solver="lbfgs", max_iter=1000, random_state=42)
        if classifier == "logistic_regression"
        else LinearSVC(C=c, dual="auto", max_iter=5000, random_state=42)
    )
    return Pipeline(
        [
            ("preprocess", TextPreprocessor(**(preprocess or DEFAULT_PREPROCESS))),
            ("features", vectorizer),
            ("classifier", model),
        ],
        memory=memory,
    )


def load_split(root: Path, name: str, manifest: dict) -> list[dict[str, str]]:
    if name not in {"train", "validation"}:
        raise ValueError("G2 may only read train and validation splits")
    path = root / "data" / "processed" / f"{name}.csv"
    if sha256_file(path) != manifest["output_sha256"][name]:
        raise ValueError(f"Split hash mismatch: {path}")
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["sample_id", "instruction", "intent"]:
            raise ValueError(f"Unexpected columns in {name}: {reader.fieldnames}")
        rows = list(reader)
    if len(rows) != manifest["counts"][name]:
        raise ValueError(f"Split row-count mismatch: {name}")
    return rows


def scores(y_true: list[str], y_pred: list[str]) -> dict[str, float]:
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 6),
        "macro_precision": round(float(precision), 6),
        "macro_recall": round(float(recall), 6),
        "macro_f1": round(float(f1), 6),
    }


def _write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _write_confusion(path: Path, labels: list[str], y_true: list[str], y_pred: list[str]) -> None:
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["true\\predicted", *labels])
        for label, row in zip(labels, matrix):
            writer.writerow([label, *row])


def _selection_key(result: dict) -> tuple[float, float, float]:
    return (result["macro_f1"], result["accuracy"], -result["C"])


def _fit_and_predict(pipeline: Pipeline, train_x, train_y, val_x):
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always", ConvergenceWarning)
        started = time.perf_counter()
        pipeline.fit(train_x, train_y)
        fit_seconds = time.perf_counter() - started
    started = time.perf_counter()
    prediction = pipeline.predict(val_x).tolist()
    predict_seconds = time.perf_counter() - started
    return prediction, fit_seconds, predict_seconds, [str(w.message) for w in captured if issubclass(w.category, ConvergenceWarning)]


def _error_report(path: Path, rows: list[dict[str, str]], predictions: list[str], selected: dict) -> None:
    errors: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row, predicted in zip(rows, predictions):
        if row["intent"] != predicted:
            errors[(row["intent"], predicted)].append(row["instruction"])
    ranked = sorted(errors.items(), key=lambda item: (-len(item[1]), item[0]))[:10]
    lines = [
        "# Validation error analysis — G2",
        "",
        f"Selected among E1–E4: **{selected['experiment']}**, C={selected['C']}, macro-F1={selected['macro_f1']:.4f}.",
        "",
        "This is an initial qualitative pass on validation only. Do not use the test split for model changes.",
        "",
        "| True intent | Predicted intent | Count |",
        "| --- | --- | ---: |",
        *(f"| {true} | {pred} | {len(texts)} |" for (true, pred), texts in ranked),
        "",
        "## Representative mistakes",
        "",
    ]
    for (true, pred), texts in ranked[:5]:
        lines.append(f"### {true} → {pred} ({len(texts)})")
        lines.append("")
        lines.extend(f"- {text}" for text in texts[:3])
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _comparison_report(path: Path, best_rows: list[dict], candidates: list[dict], ablations: list[dict], c_values: tuple[float, ...]) -> None:
    lines = [
        "# G2 validation comparison",
        "",
        f"All experiments use the frozen train/validation split, the same preprocessing configuration, unigram+bigrams, min_df=2, max_features=50,000, and C grid {list(c_values)}. Vectorizers are fitted inside the pipeline on train only. Test and challenge-final are untouched.",
        "",
        "## Best C per experiment",
        "",
        "| Experiment | Representation | Classifier | C | Accuracy | Macro-P | Macro-R | Macro-F1 | Features |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in best_rows:
        lines.append(
            f"| {row['experiment']} | {row['representation']} | {row['classifier']} | {row['C']} | "
            f"{row['accuracy']:.4f} | {row['macro_precision']:.4f} | {row['macro_recall']:.4f} | "
            f"{row['macro_f1']:.4f} | {row['feature_count']:,} |"
        )
    fixed_c = 1.0 if 1.0 in c_values else c_values[0]
    fixed = [row for row in candidates if row["C"] == fixed_c]
    lines.extend([
        "",
        f"## Controlled comparison at C={fixed_c:g}",
        "",
        "| Experiment | Macro-F1 | Accuracy |",
        "| --- | ---: | ---: |",
        *(f"| {row['experiment']} | {row['macro_f1']:.4f} | {row['accuracy']:.4f} |" for row in fixed),
        "",
        "## Preprocessing ablation on the selected E1–E4 family",
        "",
        "| Variant | Macro-F1 | Δ vs full | Accuracy |",
        "| --- | ---: | ---: | ---: |",
    ])
    full = next(row for row in ablations if row["variant"] == "full")
    for row in ablations:
        lines.append(
            f"| {row['variant']} | {row['macro_f1']:.4f} | {row['macro_f1'] - full['macro_f1']:+.4f} | {row['accuracy']:.4f} |"
        )
    lines.extend([
        "",
        "The whitespace-tokenizer ablation replaces the custom regex/placeholder tokenizer with whitespace splitting; tokenization remains necessary for word features. The no-normalization ablation disables Unicode/case/whitespace/contraction normalization. No-lemma keeps tokenization but omits POS-aware WordNet lemmatization.",
        "",
        "Fit durations include cache effects and are not a fair training-speed comparison. Inference latency and final test evaluation belong to G3.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def run(root: Path, c_values: tuple[float, ...] = (0.1, 1.0, 10.0)) -> dict:
    if not c_values or any(c <= 0 for c in c_values):
        raise ValueError("C grid must contain positive values")
    split_manifest = json.loads((root / "reports" / "split_report.json").read_text(encoding="utf-8"))
    if split_manifest["source_sha256"] != SHA256 or split_manifest.get("status") != "frozen_before_model_training":
        raise ValueError("G1 split manifest is not frozen or source hash changed")
    train = load_split(root, "train", split_manifest)
    validation = load_split(root, "validation", split_manifest)
    train_x = [row["instruction"] for row in train]
    train_y = [row["intent"] for row in train]
    val_x = [row["instruction"] for row in validation]
    val_y = [row["intent"] for row in validation]
    labels = sorted(set(train_y))
    if set(val_y) != set(labels):
        raise ValueError("Validation label set differs from training")

    report_dir = root / "reports" / "g2"
    model_dir = root / "artifacts" / "g2"
    report_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    memory = Memory(root / "artifacts" / "cache" / "g2", verbose=0)
    candidates = []
    best_rows = []
    best_predictions = {}

    for experiment, (representation, classifier) in EXPERIMENTS.items():
        best_result = None
        best_pipeline = None
        best_prediction = None
        for c in c_values:
            pipeline = build_pipeline(representation, classifier, c, memory=memory)
            prediction, fit_seconds, predict_seconds, convergence_warnings = _fit_and_predict(
                pipeline, train_x, train_y, val_x
            )
            result = {
                "experiment": experiment,
                "representation": representation,
                "classifier": classifier,
                "C": float(c),
                **scores(val_y, prediction),
                "feature_count": len(pipeline.named_steps["features"].vocabulary_),
                "fit_seconds": round(fit_seconds, 3),
                "validation_batch_seconds": round(predict_seconds, 3),
                "convergence_warnings": convergence_warnings,
            }
            candidates.append(result)
            print(f"{experiment} C={c:g} macro-F1={result['macro_f1']:.4f} accuracy={result['accuracy']:.4f}", flush=True)
            if best_result is None or _selection_key(result) > _selection_key(best_result):
                best_result, best_pipeline, best_prediction = result, pipeline, prediction
        assert best_result is not None and best_pipeline is not None and best_prediction is not None
        best_pipeline.memory = None
        model_path = model_dir / f"{experiment}.joblib"
        joblib.dump(best_pipeline, model_path, compress=3)
        loaded = joblib.load(model_path)
        if loaded.predict(val_x[:10]).tolist() != best_prediction[:10]:
            raise AssertionError(f"Reloaded {experiment} differs from fitted model")
        best_result = {**best_result, "model_file": str(model_path.relative_to(root)), "model_sha256": sha256_file(model_path), "model_bytes": model_path.stat().st_size}
        best_rows.append(best_result)
        best_predictions[experiment] = best_prediction
        _write_csv(
            report_dir / f"{experiment}_validation_predictions.csv",
            [
                {"sample_id": row["sample_id"], "instruction": row["instruction"], "true_intent": row["intent"], "predicted_intent": predicted}
                for row, predicted in zip(validation, best_prediction)
            ],
            ["sample_id", "instruction", "true_intent", "predicted_intent"],
        )
        (report_dir / f"{experiment}_per_class.json").write_text(
            json.dumps(classification_report(val_y, best_prediction, labels=labels, zero_division=0, output_dict=True), indent=2) + "\n",
            encoding="utf-8",
        )
        _write_confusion(report_dir / f"{experiment}_confusion.csv", labels, val_y, best_prediction)

    selected = max(best_rows, key=lambda row: (row["macro_f1"], row["accuracy"], -int(row["experiment"][1:])))
    ablations = [{"variant": "full", "experiment": selected["experiment"], "C": selected["C"], **{key: selected[key] for key in ("accuracy", "macro_precision", "macro_recall", "macro_f1")}}]
    for variant, preprocess in ABLATIONS.items():
        pipeline = build_pipeline(selected["representation"], selected["classifier"], selected["C"], preprocess=preprocess, memory=memory)
        prediction, fit_seconds, predict_seconds, convergence_warnings = _fit_and_predict(pipeline, train_x, train_y, val_x)
        result = {"variant": variant, "experiment": selected["experiment"], "C": selected["C"], **scores(val_y, prediction), "fit_seconds": round(fit_seconds, 3), "validation_batch_seconds": round(predict_seconds, 3), "convergence_warnings": convergence_warnings}
        ablations.append(result)
        print(f"ablation {variant} macro-F1={result['macro_f1']:.4f}", flush=True)

    _write_csv(
        report_dir / "candidate_results.csv",
        [{key: row[key] for key in ("experiment", "representation", "classifier", "C", "accuracy", "macro_precision", "macro_recall", "macro_f1", "feature_count", "fit_seconds", "validation_batch_seconds") } for row in candidates],
        ["experiment", "representation", "classifier", "C", "accuracy", "macro_precision", "macro_recall", "macro_f1", "feature_count", "fit_seconds", "validation_batch_seconds"],
    )
    (report_dir / "candidate_results.json").write_text(json.dumps(candidates, indent=2) + "\n", encoding="utf-8")
    (report_dir / "best_by_experiment.json").write_text(json.dumps(best_rows, indent=2) + "\n", encoding="utf-8")
    (report_dir / "ablation.json").write_text(json.dumps(ablations, indent=2) + "\n", encoding="utf-8")
    _error_report(report_dir / "error_analysis.md", validation, best_predictions[selected["experiment"]], selected)
    _comparison_report(report_dir / "comparison.md", best_rows, candidates, ablations, c_values)
    manifest = {
        "status": "validation_only_g2",
        "selected_from_e1_to_e4": selected["experiment"],
        "selection_metric": "validation_macro_f1",
        "split_version": split_manifest["split_version"],
        "split_sha256": {name: split_manifest["output_sha256"][name] for name in ("train", "validation")},
        "test_split_used": False,
        "challenge_final_used": False,
        "preprocessing": DEFAULT_PREPROCESS,
        "feature_config": {"ngram_range": [1, 2], "min_df": 2, "max_features": 50000},
        "C_grid": list(c_values),
        "labels": labels,
        "versions": {"python": platform.python_version(), "scikit_learn": sklearn.__version__, "nltk": nltk.__version__, "numpy": numpy.__version__, "scipy": scipy.__version__, "joblib": joblib.__version__},
        "platform": platform.platform(),
    }
    (report_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {"selected": selected, "best_by_experiment": best_rows, "ablations": ablations}
