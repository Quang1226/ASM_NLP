# G5 handoff — resume on 29 October 2026

Read this file at the start of the next working session. Workspace: `/Users/duyquang/Documents/NLP_ASM`.

## State at handoff (28 October 2026)

- G1–G4 are complete. G3's E5 model, thresholds, test evaluation and challenge-final evaluation are frozen. Do **not** select or retune a model using test or challenge-final results.
- The student approved all 27 intent responses and all four fallback responses for Demo Tech Store. `data/kb/tech_store_kb.json` records approval; see `reports/g5/kb_approval.md` for the hash and evidence. Ghost-UI wording was replaced with explicit real-store or simulated-process wording.
- The existing local demo SQLite seed replies refreshed on API restart: 27/27 match the approved KB. The browser chat returned the approved `KB-TRACK-ORDER` response. All 17 tests passed.
- The latest G4 UI is white/technology blue with the old-style widget, admin workspace, semantic action colors, AI diagnostics, contextual clarify chips and 13px chat text. See `reports/g4/implementation.md`.
- No Git repository exists yet in `NLP_ASM`; the student said they would create it. No root `requirements.txt` exists yet. No final report PDF or demo video exists yet.
- Official deadline reported by the student: **30 November 2026**. The Google Form reportedly accepts one file up to 100 MB. Whether a PDF containing GitHub/video links satisfies the source/demo submission requirement remains to be confirmed with the instructor.

## First work tomorrow

1. Read this handoff, `docs/planning/IMPLEMENTATION_PLAN.md` (G5), `reports/g3/final_report.md`, `reports/g4/implementation.md`, and `reports/g5/kb_approval.md`.
2. Build the **English report outline and evidence map** for the required eight sections: Introduction, Related Work, Dataset Description, Methodology, Experiments, Results, Error Analysis, Conclusion. Map every reported number and figure to an existing artifact before drafting prose. Include the one-student/100% contribution statement.
3. Ask the student only for genuinely missing report details, especially their preferred name/student ID and any instructor guidance on the one-file submission. Continue report work while waiting for answers.

## Remaining G5 checklist, in dependency order

- [ ] Draft and verify the eight-section report. Use the frozen G1–G3 counts and metrics; include per-class results, confusion matrix, representative errors, model size/latency, Bitext template limitations, and the disclosed challenge-final limitation (13/22 actions; not fully blind). Explain G4 as a local simulated application, not a production customer-service system.
- [ ] Create a root `requirements.txt` with direct, pinned project dependencies consistent with `pyproject.toml`; do not dump the whole local environment with `pip freeze`. Test installation and reproducibility in a clean environment.
- [ ] Finish the English README for an external marker: purpose, architecture, pinned Bitext/encoder provenance and licenses, setup, exact data/training/evaluation/demo commands, verified results, model/KB limitations, and reused-code provenance. Do not re-evaluate the held-out test to choose a model.
- [ ] Prepare a short demo script and capture guide/clarify/scope-boundary/handoff plus diagnostics and admin knowledge views using fake data. Record and host the video only after the student agrees on destination/account; include the final link in the report.
- [ ] After the student creates the Git repository, inspect ignore rules and repository size; commit or push only with user authorization. Link a fixed commit/tag in the report rather than a moving branch URL.
- [ ] Build the final PDF, visually inspect all pages, verify links and all numeric claims, and include the one-member/100% contribution table.
- [ ] Validate a fresh setup: install, tests, frontend build, actual model/API/chat, and absence of secrets, personal contact records, old VNJ DB, caches and unnecessary large artifacts from the submission package.
- [ ] Confirm the instructor's rule for one uploaded file. Preferred if allowed: PDF under 100 MB with fixed GitHub and demo-video links. If source must be inside the upload and ZIP is accepted: one ZIP containing PDF plus safe source. Do not submit until the route is confirmed.

## Important source files

- Frozen numbers and limitations: `reports/g3/final_report.md`, `reports/g3/final_evaluation.json`, `reports/g3/frozen_bundle.json`.
- Dataset and split: `reports/data_audit.json`, `docs/planning/DATA_PREPARATION_GUIDE.md`, `docs/planning/data_audit.md`.
- Demo and KB: `reports/g4/implementation.md`, `data/kb/tech_store_kb.json`, `docs/planning/CODE_REUSE_G4.md`.
- Submission plan: `docs/planning/IMPLEMENTATION_PLAN.md` §G5; assignment PDF at `docs/assignment/mlAssignments_v1.1_english.pdf`.

## Completion criterion

Another person can follow the README to reproduce the experiments and run the local demo; the report matches frozen artifacts; the final single uploaded file satisfies the Google Form's format and 100 MB limit.
