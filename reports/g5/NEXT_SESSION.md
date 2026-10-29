# G5 status — 29 October 2026

Read this file at the start of the next working session. Workspace: `/Users/duyquang/Documents/NLP_ASM`.

## Current state

- G1–G4 are complete. G3's E5 model, thresholds, test evaluation and challenge-final evaluation are frozen. Do **not** select or retune a model using test or challenge-final results.
- The student approved all 27 intent responses and all four fallback responses for Demo Tech Store. `data/kb/tech_store_kb.json` records approval; see `reports/g5/kb_approval.md` for the hash and evidence. Ghost-UI wording was replaced with explicit real-store or simulated-process wording.
- The existing local demo SQLite seed replies refreshed on API restart: 27/27 match the approved KB. The browser chat returned the approved `KB-TRACK-ORDER` response. All 17 tests passed.
- The latest G4 UI is white/technology blue with the old-style widget, admin workspace, semantic action colors, AI diagnostics, contextual clarify chips and 13px chat text. See `reports/g4/implementation.md`.
- Git repository `Quang1226/ASM_NLP` has a first commit, `a81b9d14f273456654eb7c719b1dd9c20680813b`. The root `requirements.txt`, English README, report drafts, and detailed demo script exist. The final report PDF and demo video do not yet exist.
- A fresh Python environment installed dependencies and passed 17 tests. A temporary empty clone reproduced split hashes, E1–E5 validation results, E5 artifact hashes, and a real-model API/chat response. Frontend `npm ci`, build, and audit passed after updating Vite to 8.3.5. See `reports/g5/submission_readiness_check.md`.
- The Vite package files, Python dependency pins, data-download fix, model-restoration script, README, and G5 reports have uncommitted local changes. A final fixed commit or tag must be created after these and the final submission files are pushed.
- Official deadline reported by the student: **30 November 2026**. The Google Form reportedly accepts one file up to 100 MB. Whether a PDF containing GitHub/video links satisfies the source/demo submission requirement remains to be confirmed with the instructor.

## Remaining G5 checklist, in dependency order

- [x] Draft the eight-section English report and Vietnamese summary from frozen G1–G4 evidence. Include per-class results, confusion matrix, errors, latency, and disclosed challenge-final limits.
- [x] Create root `requirements.txt` with direct pins matching `pyproject.toml`; install it in a fresh Python environment.
- [x] Finish the English README with source and encoder provenance, setup, commands, results, demo, limits, and code-reuse record.
- [x] Prepare the detailed demo script and verify four route prompts against the real API.
- [ ] **Student:** record and host the demo video; add its final link to the report.
- [x] Inspect the Git repository, ignore rules, tracked file size, and first fixed commit.
- [ ] Push the latest G5 documentation and Vite dependency fix, then replace the report's first-commit link with a final fixed commit or tag.
- [ ] **Student / report finalization:** provide name and student ID; build and visually inspect the final PDF, verify links and numbers, and complete the one-member/100% contribution table.
- [x] Validate fresh dependency installation, 17 tests, frontend clean install/build, real model/API/chat, and tracked-file privacy/size scan. See the readiness report.
- [x] Reproduce data preparation and E1–E5 from an empty clone. The restored E5 artifacts matched frozen hashes and served chat. The held-out test and challenge-final reports were not rerun.
- [ ] **Student:** confirm the instructor's current upload route and one-file rule. Then assemble a compliant file under 100 MB.

## Important source files

- Frozen numbers and limitations: `reports/g3/final_report.md`, `reports/g3/final_evaluation.json`, `reports/g3/frozen_bundle.json`.
- Dataset and split: `reports/data_audit.json`, `docs/planning/DATA_PREPARATION_GUIDE.md`, `docs/planning/data_audit.md`.
- Demo and KB: `reports/g4/implementation.md`, `data/kb/tech_store_kb.json`, `docs/planning/CODE_REUSE_G4.md`.
- Submission plan: `docs/planning/IMPLEMENTATION_PLAN.md` §G5; assignment PDF at `docs/assignment/mlAssignments_v1.1_english.pdf`.

## Completion criterion

Another person can follow the README to reproduce the experiments and run the local demo; the report matches frozen artifacts; the final uploaded file satisfies the instructor's current route and 100 MB limit. This gate remains open until the unchecked items above are complete.
