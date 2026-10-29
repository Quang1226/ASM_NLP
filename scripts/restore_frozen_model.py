"""Recreate ignored E5 runtime files without changing frozen evaluation reports."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from intent_support.data.bitext import sha256_file
from intent_support.experiments.g3_embedding import run


def main() -> None:
    frozen = json.loads((ROOT / "reports/g3/frozen_bundle.json").read_text())
    targets = [frozen["classifier"], frozen["train_embedding"], frozen["validation_embedding"]]
    if all((ROOT / item["model_file" if "model_file" in item else "file"]).exists() and
           sha256_file(ROOT / item["model_file" if "model_file" in item else "file"]) ==
           item["model_sha256" if "model_file" in item else "file_sha256"] for item in targets):
        print("Frozen E5 runtime files already match the bundle")
        return

    with TemporaryDirectory(prefix="nlp_asm_e5_restore_") as directory:
        scratch = Path(directory)
        for relative in ("reports/split_report.json", "data/processed/train.csv", "data/processed/validation.csv"):
            destination = scratch / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, destination)
        recreated = run(scratch)
        for key in ("classifier", "train_embedding", "validation_embedding"):
            actual = recreated["selected" if key == "classifier" else key]
            expected = frozen[key]
            hash_key = "model_sha256" if key == "classifier" else "file_sha256"
            if actual[hash_key] != expected[hash_key]:
                raise ValueError(f"Recreated {key} does not match frozen SHA-256; check pinned dependencies")
        for key in ("classifier", "train_embedding", "validation_embedding"):
            entry = frozen[key]
            relative = entry["model_file" if key == "classifier" else "file"]
            destination = ROOT / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(scratch / relative, destination)
            if key != "classifier":
                shutil.copy2((scratch / relative).with_suffix(".json"), destination.with_suffix(".json"))
    print("Restored frozen E5 runtime files; final test and challenge reports were untouched")


if __name__ == "__main__":
    main()
