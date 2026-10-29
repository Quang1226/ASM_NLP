# Intent-Aware Customer Support Chatbot

NLP course project: compare text representations and trained intent classifiers, then use the selected model in an English customer-support demo. The product uses a simulated consumer-technology store; it does not perform real account or order operations.

## Current status

Gates G1–G4 are complete. E5 is the frozen intent model. The local API, storefront, chat widget, and admin workspace are implemented. G5 report and submission packaging are in progress.

## Clean setup for a marker

Use Python 3.12 and Node.js with npm. The commands below start from this project root. Python packages need PyPI access. The first data and encoder downloads need Hugging Face access. Disk space must also cover the encoder, the training embedding bank, and local datasets.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/python scripts/setup_nltk_data.py
.venv/bin/python scripts/fetch_data.py
.venv/bin/python scripts/audit_data.py
.venv/bin/python scripts/split_data.py
.venv/bin/python scripts/audit_split_similarity.py
.venv/bin/python scripts/audit_challenge.py
.venv/bin/python scripts/audit_data.py
.venv/bin/python scripts/train_g2.py
.venv/bin/python scripts/train_e5.py
```

The raw CSV is checked against a pinned SHA-256. The split script checks its frozen input and configuration. `train_e5.py` downloads the pinned encoder once. Do not rerun `freeze_g3.py` or `evaluate_g3_final.py` in this checkout: their existing frozen reports are the one-time final evaluation. Those scripts refuse to overwrite it. Check their saved hashes in `reports/g3/frozen_bundle.json` and `reports/g3/final_evaluation.json`.

Check the local app after training:

```bash
.venv/bin/python -m pip install 'pytest>=8,<10'
.venv/bin/python -m pytest -q
cd frontend && npm ci && npm run build
```

Set private admin credentials in your shell, then start the API and frontend as described under **G4 local demo**. Visit `/api/health` to confirm model and KB readiness. Admin access returns HTTP 401 without a valid token. `data/demo/demo_store.sqlite` contains local demo records and must not be submitted.

## Layout

- `docs/assignment/`: course brief.
- `docs/planning/`: blueprint, codebase analysis and implementation plan.
- `data/raw/`: downloaded source data (ignored by Git).
- `data/processed/`: derived splits (ignored by Git; regenerate with scripts).
- `data/challenge/`: approved AI-assisted challenge set and locked manifest.
- `data/kb/`: simulated store policies and intent responses.
- `data/kb/tech_store_kb.json`: student-approved English policy and response mapping for all 27 intents plus four fallback replies.
- `src/intent_support/`: reusable NLP code.
- `scripts/`: reproducible command-line steps.
- `reports/`: data and experiment reports.
- `backend/`, `frontend/`: local demo application.

## Data preparation

The source is [Bitext Customer Support](https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset), pinned to revision `430d1a89bd93bd1fa23c16f29dd53e73f0087443`. The source CSV SHA-256 is `6f81102b0100b97b8468eb04368033a23206bf1fde9d53500d5806ec1001a434`. The dataset is hybrid synthetic. Its publisher lists the CDLA-Sharing-1.0 license. The original `response` column is not used as a model feature or store policy.

```bash
python3 scripts/fetch_data.py
python3 scripts/audit_data.py
python3 scripts/split_data.py
python3 scripts/audit_split_similarity.py
python3 scripts/audit_challenge.py
python3 scripts/audit_data.py  # refreshes the post-split summary
```

The fetch script verifies the exact SHA-256 of the pinned CSV. Audit outputs go to `reports/`; splits go to `data/processed/`. The split script deduplicates requests after Unicode, case, punctuation and whitespace normalization, groups likely near-duplicate requests within each intent, and excludes any holdout row with an exhaustive same-intent `SequenceMatcher` match at 0.90 or higher in an earlier split. Lower-similarity paraphrases may remain; the reports record this limitation and class imbalance.

See `docs/planning/DATA_PREPARATION_GUIDE.md` for the current counts, decisions and student review points.

## G2 experiments

Use the clean setup above. WordNet and the English POS tagger are downloaded from the [official NLTK data repository](https://github.com/nltk/nltk_data) and checked against their published SHA-256 values.

```bash
.venv/bin/python scripts/setup_nltk_data.py
.venv/bin/python scripts/train_g2.py
.venv/bin/python -m unittest discover -s tests -v
```

On Windows, use `.venv\\Scripts\\python` in place of `.venv/bin/python`. The G2 script trains E1–E4 (BoW/TF-IDF × Logistic Regression/Linear SVM) on the frozen train split, selects C from `{0.1, 1, 10}` using validation macro-F1, and runs one-factor preprocessing ablations. It never opens the test split or the final challenge partition. Reports are in `reports/g2/`; local model artifacts are in `artifacts/g2/` and are ignored by Git. Their hashes are recorded in the reports.

The leading E3 and E4 validation macro-F1 scores are almost identical. These high results are from a hybrid synthetic dataset and do not establish production performance.

## G3 embedding experiment

E5 uses the frozen [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) encoder (Apache-2.0, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`) to make 384-dimensional normalized sentence embeddings. It then trains Logistic Regression on the same frozen train split and selects C on validation. Embeddings are cached under `artifacts/g3/` using dataset and model hashes; this cache is ignored by Git. The encoder is downloaded once from Hugging Face on a fresh setup, then can run from the local cache with `HF_HUB_OFFLINE=1`. The `sentence-transformers` dependency is pinned in `pyproject.toml`.

```bash
.venv/bin/python scripts/train_e5.py
.venv/bin/python scripts/freeze_g3.py
.venv/bin/python scripts/evaluate_g3_final.py
```

These three commands document the original G3 order. In this checkout, run `train_e5.py` to recreate local model files, but keep the existing frozen and final reports. `freeze_g3.py` uses only validation and approved challenge `tuning` rows. `evaluate_g3_final.py` refuses a repeat once the final report exists. See `reports/g3/` for classifier, policy, predictions, and limits. Classifier probability is **not** a calibrated in-scope probability. Scope decisions also check maximum cosine similarity to frozen training embeddings.

| Model | Representation and classifier | Validation macro-F1 |
| --- | --- | ---: |
| E1 | BoW + Logistic Regression | 0.980507 |
| E2 | BoW + Linear SVM | 0.982836 |
| E3 | TF-IDF + Logistic Regression | 0.984594 |
| E4 | TF-IDF + Linear SVM | 0.984585 |
| E5 | Fixed MiniLM embeddings + Logistic Regression | 0.989829 |

The selected E5 has held-out Bitext test accuracy **0.988106** and macro-F1 **0.985686** (3,447 cases). The per-class report and full confusion matrix are in `reports/g3/`. Its challenge-final result is **11/14** correct in-scope intents and **13/22** correct actions. The challenge result limits claims about real customer requests. Some ambiguous requests are still answered; some valid requests trigger clarification. The full breakdown is in `reports/g3/final_report.md`. The encoder weights (~91 MB) and training embedding bank (~26 MB) are local runtime dependencies, not submission files.

The challenge-final rows were displayed once during initial schema inspection before the bundle was frozen. They were not used by the selection code, but this means the challenge-final score is exploratory rather than a fully blind holdout. The Bitext test set remained blind until the one-time final evaluation.

On an Apple Silicon CPU, the measured E5 path had median latency 8.382 ms and p95 9.500 ms. It includes encoding, classification, train-bank cosine search, and action selection. Model load was measured separately at 0.449 seconds. These are machine-specific figures, not a latency guarantee.

## G4 local demo

The frontend recreates the old chatbot's floating chat widget and admin functions in a new English Demo Tech Store interface. It includes open/minimize/close, suggested questions, a developer-only intent inspector, new chat, an explicit contact form, admin login, knowledge create/edit/delete, opt-in contacts, and protected conversation history. Source reuse is documented in `docs/planning/CODE_REUSE_G4.md`.

The backend loads the frozen G3 model once at startup. Its deterministic path is `predict -> decide -> retrieve from KB -> respond`; no paid LLM API or old VNJ database is used. The local SQLite database is created at `data/demo/demo_store.sqlite` and ignored by Git. The 27 approved seed responses come from `data/kb/tech_store_kb.json`; source-managed seed wording refreshes when the API restarts, while admin-edited entries, custom answers, and deleted seeds remain local to the SQLite database. A missing model/KB returns a clear unavailable state; a missing active intent answer falls back to clarification. Self-repair requests for hardware use the `KB-REPAIR` boundary. This product rule is separate from the frozen G3 evaluation.

After completing the G1–G3 setup above, start the API and frontend in separate terminals:

```bash
# Terminal 1 — use your own local credentials; do not commit them.
export DEMO_ADMIN_USERNAME='your_admin_name'
export DEMO_ADMIN_PASSWORD='your_private_password'
HF_HUB_OFFLINE=1 .venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Terminal 2
cd frontend
npm ci
npm run dev
```

Open `http://127.0.0.1:5173/` for the storefront/chat and `http://127.0.0.1:5173/admin` for the admin workspace. `HF_HUB_OFFLINE=1` works after the pinned Hugging Face model has been downloaded by `train_e5.py`; omit it for the first download. The frontend proxies `/api` to port 8000 during development. There are no default admin credentials. The contact form stores only a visitor's explicit submission in this local demo; it does not notify a real person. Messages and contact details stay in the local SQLite file; do not distribute that file.

Run checks with `.venv/bin/python -m pytest -q` and `cd frontend && npm run build`.

## Submission

The student reported a **30 November 2026** deadline and a Google Form accepting one file up to **100 MB**. The assignment PDF instead names a shared Google Drive folder. Confirm the current LMS instructions before submission. If links are accepted, the planned file is a report PDF with fixed Git commit/tag and demo-video links. Otherwise, use the instructor's specified source-code format. Keep raw data, model caches, local SQLite records, secrets, and the old VNJ database out of any uploaded package.

The full English report draft is `reports/g5/report_en_full.md`. A shorter Vietnamese summary is `reports/g5/report_vi_summary.md`. The planned demo sequence is in `reports/g5/demo_script.md`.
