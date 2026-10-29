# Demo Tech Store knowledge-base approval

**Approved by the student:** 28 October 2026, in five intent groups plus four fallback replies.

- All 27 intent responses in `data/kb/tech_store_kb.json` use the English wording reviewed in the conversation. The four fallback responses were approved and left unchanged.
- The simulated rules and stable `POL-*`/`KB-*` references remain intact. Four policy descriptions were clarified to distinguish hypothetical checkout, account and invoice flows from features that actually exist in the demo.
- The response wording does not direct visitors to a working Order history, Account settings, invoice page, or checkout. The bot cannot perform real order, payment, refund, account or agent operations.
- `store.intent_response_review_status` and `store.fallback_review_status` are `approved_by_student_2026-10-28`.
- SHA-256 of the approved JSON: `85f27701af27a95f240727cf1f000dc7a4dfd6c7776819b7ad875838d1892bea`.

**Verification:** All 17 project tests passed. On API restart, all 27 source-managed seed replies in the existing local demo database matched the approved JSON. A browser chat request about order status returned the approved `KB-TRACK-ORDER` wording. Admin-edited seed entries and custom answers remain local and are not overwritten by later KB source refreshes.
