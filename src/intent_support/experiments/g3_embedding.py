"""Frozen sentence embeddings and E5 classifier selection on validation only."""

from __future__ import annotations

import csv
import json
import os
import platform
import time
from pathlib import Path

import joblib
import numpy as np
import sklearn
import sentence_transformers
import torch
from huggingface_hub import snapshot_download
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression

from intent_support.data.bitext import SHA256, sha256_file
from intent_support.experiments.g2 import load_split, scores

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
MODEL_LICENSE = "Apache-2.0"
SEED = 42
BATCH_SIZE = 64
C_GRID = (0.1, 1.0, 10.0)


def frozen_split_manifest(root: Path) -> dict:
    manifest = json.loads((root / "reports/split_report.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "frozen_before_model_training" or manifest.get("source_sha256") != SHA256:
        raise ValueError("G1 split manifest is not frozen")
    return manifest


def load_encoder() -> SentenceTransformer:
    snapshot = snapshot_download(repo_id=MODEL_ID, revision=MODEL_REVISION,
                                 local_files_only=os.environ.get("HF_HUB_OFFLINE") == "1")
    encoder = SentenceTransformer(snapshot, device="cpu", local_files_only=True)
    encoder.eval()
    return encoder


def _cache_paths(root: Path, split: str, source_hash: str) -> tuple[Path, Path]:
    import hashlib

    payload = json.dumps({
        "split": split, "split_sha256": source_hash, "model_id": MODEL_ID,
        "revision": MODEL_REVISION, "normalize_embeddings": True,
        "dtype": "float32", "sentence_transformers": sentence_transformers.__version__,
    }, sort_keys=True).encode()
    key = hashlib.sha256(payload).hexdigest()[:20]
    base = root / "artifacts/g3/embeddings" / f"{split}-{key}"
    return base.with_suffix(".npy"), base.with_suffix(".json")


def embeddings(root: Path, encoder: SentenceTransformer, split: str, texts: list[str], source_hash: str) -> tuple[np.ndarray, dict]:
    npy_path, meta_path = _cache_paths(root, split, source_hash)
    if npy_path.exists() and meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("file_sha256") == sha256_file(npy_path) and meta.get("rows") == len(texts):
            matrix = np.load(npy_path, allow_pickle=False)
            if matrix.shape == (len(texts), encoder.get_sentence_embedding_dimension()) and matrix.dtype == np.float32:
                return matrix, meta
    npy_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    matrix = encoder.encode(texts, batch_size=BATCH_SIZE, convert_to_numpy=True,
                            normalize_embeddings=True, show_progress_bar=True).astype(np.float32, copy=False)
    if matrix.shape != (len(texts), 384) or not np.isfinite(matrix).all():
        raise ValueError("Unexpected E5 embedding shape or non-finite values")
    np.save(npy_path, matrix, allow_pickle=False)
    meta = {
        "split": split, "rows": len(texts), "dimensions": matrix.shape[1],
        "split_sha256": source_hash, "model_id": MODEL_ID, "revision": MODEL_REVISION,
        "license": MODEL_LICENSE, "batch_size": BATCH_SIZE, "device": "cpu",
        "normalized": True, "encode_seconds": round(time.perf_counter() - started, 3),
        "file": str(npy_path.relative_to(root)), "file_sha256": sha256_file(npy_path),
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return matrix, meta


def run(root: Path) -> dict:
    if (root / "reports/g3/frozen_bundle.json").exists():
        raise FileExistsError("G3 bundle is frozen; E5 may not be retrained in place")
    manifest = frozen_split_manifest(root)
    train = load_split(root, "train", manifest)
    validation = load_split(root, "validation", manifest)
    encoder = load_encoder()
    train_x, train_meta = embeddings(root, encoder, "train", [r["instruction"] for r in train], manifest["output_sha256"]["train"])
    val_x, val_meta = embeddings(root, encoder, "validation", [r["instruction"] for r in validation], manifest["output_sha256"]["validation"])
    train_y, val_y = [r["intent"] for r in train], [r["intent"] for r in validation]
    results = []
    best = None
    best_model = None
    for c in C_GRID:
        model = LogisticRegression(C=c, max_iter=1000, solver="lbfgs", random_state=SEED)
        started = time.perf_counter()
        model.fit(train_x, train_y)
        fit_seconds = time.perf_counter() - started
        pred = model.predict(val_x).tolist()
        result = {"experiment": "E5", "C": c, **scores(val_y, pred), "fit_seconds": round(fit_seconds, 3)}
        results.append(result)
        print(f"E5 C={c:g} validation macro-F1={result['macro_f1']:.6f}", flush=True)
        if best is None or (result["macro_f1"], result["accuracy"], -c) > (best["macro_f1"], best["accuracy"], -best["C"]):
            best, best_model = result, model
    assert best is not None and best_model is not None
    model_path = root / "artifacts/g3/E5_classifier.joblib"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_model, model_path, compress=3)
    reloaded = joblib.load(model_path)
    if reloaded.predict(val_x[:20]).tolist() != best_model.predict(val_x[:20]).tolist():
        raise AssertionError("E5 reload changed predictions")
    report_dir = root / "reports/g3"
    report_dir.mkdir(parents=True, exist_ok=True)
    pred = best_model.predict(val_x).tolist()
    with (report_dir / "E5_validation_predictions.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["sample_id", "instruction", "true_intent", "predicted_intent"])
        writer.writerows((r["sample_id"], r["instruction"], r["intent"], p) for r, p in zip(validation, pred))
    report = {
        "model_id": MODEL_ID, "model_revision": MODEL_REVISION, "license": MODEL_LICENSE,
        "model_card": f"https://huggingface.co/{MODEL_ID}/tree/{MODEL_REVISION}",
        "encoder_input": "original instruction text, no G2 lemmatization",
        "embedding_normalized": True, "device": "cpu", "batch_size": BATCH_SIZE,
        "split_version": manifest["split_version"], "split_hashes": manifest["output_sha256"],
        "train_embedding": train_meta, "validation_embedding": val_meta,
        "candidates": results, "selected": {**best, "model_file": str(model_path.relative_to(root)),
                                    "model_sha256": sha256_file(model_path), "model_bytes": model_path.stat().st_size},
        "versions": {"python": platform.python_version(), "scikit_learn": sklearn.__version__,
                     "sentence_transformers": sentence_transformers.__version__, "torch": torch.__version__},
        "test_used": False, "challenge_final_used": False,
    }
    (report_dir / "e5_validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
