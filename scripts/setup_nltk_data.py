"""Download and verify the two NLTK resources required by G2 preprocessing."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "nltk_data"
RESOURCES = {
    "wordnet": {
        "subdir": "corpora",
        "url": "https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/wordnet.zip",
        "sha256": "cbda5ea6eef7f36a97a43d4a75f85e07fccbb4f23657d27b4ccbc93e2646ab59",
        "extract": False,
    },
    "averaged_perceptron_tagger_eng": {
        "subdir": "taggers",
        "url": "https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/taggers/averaged_perceptron_tagger_eng.zip",
        "sha256": "6025f530624335c67d6547d44757b357b4e79bae030a0383e9887a92c1718f0b",
        "extract": True,
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download(url: str, destination: Path) -> None:
    temporary = destination.with_suffix(".zip.partial")
    try:
        if shutil.which("curl"):
            subprocess.run(
                ["curl", "--fail", "--location", "--retry", "2", "--silent", "--show-error", url, "--output", str(temporary)],
                check=True,
            )
        else:
            with urllib.request.urlopen(url, timeout=120) as response, temporary.open("wb") as stream:
                shutil.copyfileobj(response, stream)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    for name, resource in RESOURCES.items():
        directory = DATA_DIR / resource["subdir"]
        directory.mkdir(parents=True, exist_ok=True)
        archive = directory / f"{name}.zip"
        if not archive.exists() or sha256(archive) != resource["sha256"]:
            download(resource["url"], archive)
        if sha256(archive) != resource["sha256"]:
            raise ValueError(f"Checksum mismatch for {archive}")
        if resource["extract"]:
            with zipfile.ZipFile(archive) as source:
                for member in source.infolist():
                    target = (directory / member.filename).resolve()
                    if not target.is_relative_to(directory.resolve()):
                        raise ValueError(f"Unsafe archive path: {member.filename}")
                source.extractall(directory)
        print(f"Verified {name}: {archive}")


if __name__ == "__main__":
    main()
