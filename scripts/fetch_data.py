"""Download the pinned public dataset and verify its content hash."""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from intent_support.data.bitext import RAW_PATH, REVISION, SHA256, URL, sha256_file


def main() -> None:
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    if RAW_PATH.exists() and sha256_file(RAW_PATH) == SHA256:
        print(f"Verified existing dataset: {RAW_PATH}")
    else:
        temporary = RAW_PATH.with_suffix(".csv.partial")
        try:
            with urllib.request.urlopen(URL, timeout=120) as response, temporary.open("wb") as output:
                while block := response.read(1024 * 1024):
                    output.write(block)
            observed = sha256_file(temporary)
            if observed != SHA256:
                raise ValueError(f"SHA-256 mismatch: expected {SHA256}, got {observed}")
            temporary.replace(RAW_PATH)
        finally:
            temporary.unlink(missing_ok=True)
        print(f"Downloaded and verified: {RAW_PATH}")

    manifest = {
        "dataset": "Bitext Customer Support LLM Chatbot Training Dataset",
        "publisher": "Bitext Innovations",
        "source_url": URL,
        "revision": REVISION,
        "sha256": SHA256,
        "size_bytes": RAW_PATH.stat().st_size,
        "license_as_listed_by_publisher": "CDLA-Sharing-1.0",
        "raw_file": "data/raw/bitext_customer_support_v11.csv",
    }
    path = ROOT / "data" / "source_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
