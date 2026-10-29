# Approved challenge set v1

`challenge_draft.csv` is an AI-assisted **44-case set approved by the student on 28 October 2026** (22 `tuning`, 22 `final`). The filename is retained for continuity; `review_status` and `challenge_manifest.json` are the approval record. It is not part of Bitext and must never be mixed into training, validation or test data. The `tuning` partition can inform the decision threshold and handling policy. The `final` partition must stay untouched until those choices are frozen. The in-scope cases cover all 27 Bitext intents; many refer to technology products to test transfer beyond Bitext's generic wording.

The draft has paraphrases, typos, negation, ambiguous requests and out-of-scope requests. `expected_intent` is blank where a single intent cannot be assigned safely. `guide` means a policy-based answer or instructions, not a claim that a real order/account action was completed. `scope_boundary` means a polite refusal outside the simulated store's support scope. `handoff` is only used where the customer explicitly requests a person; no real agent is implied unless the demo explicitly offers one.

All 44 rows are marked `approved`. Any later edit requires a new reviewed version and a new manifest hash. Do not use the `final` partition for model or threshold selection.

Run `python3 scripts/audit_challenge.py` to verify the locked hash, all-intent coverage, and source similarity of in-scope cases.
