"""Pinned Bitext source and small, dependency-free data utilities."""

from __future__ import annotations

import csv
import hashlib
import re
import unicodedata
from pathlib import Path

REVISION = "430d1a89bd93bd1fa23c16f29dd53e73f0087443"
FILENAME = "Bitext_Sample_Customer_Support_Training_Dataset_27K_responses-v11.csv"
URL = (
    "https://huggingface.co/datasets/bitext/"
    "Bitext-customer-support-llm-chatbot-training-dataset/resolve/"
    f"{REVISION}/{FILENAME}"
)
SHA256 = "6f81102b0100b97b8468eb04368033a23206bf1fde9d53500d5806ec1001a434"
REQUIRED_COLUMNS = ("flags", "instruction", "category", "intent", "response")
ROOT = Path(__file__).resolve().parents[3]
RAW_PATH = ROOT / "data" / "raw" / "bitext_customer_support_v11.csv"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_instruction(text: str) -> str:
    """Case/space/punctuation-insensitive grouping key, not model preprocessing."""
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"[^a-z0-9]+", " ", normalized).strip()


def read_rows(path: Path = RAW_PATH) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}; run python3 scripts/fetch_data.py")
    if sha256_file(path) != SHA256:
        raise ValueError(f"SHA-256 mismatch for {path}; refusing to analyze a changed dataset")
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None or tuple(reader.fieldnames) != REQUIRED_COLUMNS:
            raise ValueError(f"Unexpected Bitext columns: {reader.fieldnames}")
        return list(reader)
