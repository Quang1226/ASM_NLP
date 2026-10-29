# G5 item 7 — clean setup and package-content check

**Checked:** 29 October 2026. **Workspace:** `NLP_ASM`. This check covers installation, tests, build, actual-model API behavior, and files Git would include. It does not freeze the final submission package.

## Execution results

| Check | Result | Evidence |
| --- | --- | --- |
| Fresh Python 3.12 virtual environment | Pass | Created outside the project at `/private/tmp/nlp_asm_clean_venv`; `pip install -r requirements.txt`, editable project install, and `pip check` succeeded. Model-critical libraries were later pinned to the original versions. |
| NLTK resources | Pass | `scripts/setup_nltk_data.py` verified WordNet and the English POS tagger checksums. |
| Python tests | Pass | `pytest -q`: 17 passed. One Starlette `TestClient` deprecation warning; no test failures. |
| Frontend clean install | Pass after lockfile repair | `npm ci` initially failed because `@emnapi/wasi-threads@1.2.3` was absent from the lockfile. The lockfile was updated. A new `npm ci` then succeeded. |
| Frontend production build | Pass | Vite 8.3.5 built 1,744 modules with `npm run build`. |
| Frontend dependency audit | Pass | `npm audit --audit-level=high` reported zero vulnerabilities after a compatible Vite and transitive dependency update. |
| Frozen model load | Pass | The clean Python environment loaded bundle `g3-v1-2026-10-28`. A fresh clone also rebuilt runtime artifacts with hashes matching the frozen bundle. |
| API and chat with real model | Pass | FastAPI `TestClient` used the real model and a disposable SQLite file. Health returned 200/ready. Guide, clarify, scope boundary, and handoff returned the expected action and KB reference. |
| Admin access | Pass | Knowledge endpoint without a token returned 401. Test-only admin login succeeded; the protected KB returned 27 entries. |

The API smoke test used these artificial requests: shipping options for a graphics card; a pending laptop order; the causes of the French Revolution; and a request for a real support person. The disposable SQLite file was removed with its temporary directory. No real contact details were submitted.

## Files and privacy

- The first commit tracks 111 files. Their working-tree size is about 3.4 MiB. No tracked file exceeds 1 MiB.
- Git tracks no `.env` secret file, SQLite/DB, model weights, `.npy` embedding cache, `.venv`, `node_modules`, frontend build, or video.
- `.gitignore` excludes local raw and processed data, NLTK downloads, model artifacts, demo DB, Python caches, frontend dependencies and build output. `git ls-files -ci --exclude-standard` returned no tracked ignored files.
- A high-confidence secret-pattern scan found no private key, GitHub token, OpenAI key, or AWS access key. Two password-pattern hits were reviewed: a README placeholder and a fake test password.
- Email-like values in tracked text occur only as `demo@example.com` in API tests. Phone-like regex hits were sample IDs or synthetic order/invoice numbers from Bitext prediction files. No tracked contact export or local DB was found.
- Local large files above 10 MiB are the raw Bitext CSV, WordNet data, and train embedding bank. Git ignores all three. The old VNJ database is outside this project and is not tracked here.

## Empty-clone reproduction

A clone in `/private/tmp/nlp_asm_repro2` downloaded the pinned Bitext CSV and NLTK resources. It recreated train/validation/test with counts 16,849/3,491/3,447 and exact saved split hashes. The exhaustive same-intent cross-split check returned zero matches at 0.90. The challenge audit covered 44 cases and 27 intents.

E1–E4 reproduced their saved validation scores. E5 reproduced macro-F1 0.989829 after pinning the original model-critical versions of PyTorch, Transformers, Hugging Face Hub, NumPy, and SciPy. The E5 classifier, train embeddings, and validation embeddings matched the frozen SHA-256 values exactly. `scripts/restore_frozen_model.py` rebuilt those ignored runtime files without changing the frozen reports. The clone then returned `ready: true` and a `guide` chat response from the real API model.

The first Bitext download exposed a macOS TLS trust-store issue in the Python environment. `scripts/fetch_data.py` now uses the pinned Certifi CA bundle; the next download verified the expected source hash. The check did **not** repeat the frozen held-out test or challenge-final evaluation.

The final PDF, video, upload route, and final fixed Git commit are deferred to G5 items 6 and 8. The dependency, README, data-download, restoration-script, and report updates from this check must be committed and pushed before the final link is chosen.
