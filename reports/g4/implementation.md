# G4 local demo implementation

**Date:** 28 October 2026. **Store:** Demo Tech Store. **Mode:** local, simulated, no paid LLM API.

## What runs

- FastAPI loads the frozen G3 E5 bundle once at startup and verifies the classifier, embedding bank and bundle hashes. Requests follow `predict -> decide -> retrieve -> respond` using the local Demo Tech Store KB.
- The SQLite database at `data/demo/demo_store.sqlite` is new and ignored by Git. It stores demo sessions, chat messages, explicitly submitted contacts, and editable knowledge entries. The old VNJ database is never imported.
- The React storefront has a floating chat widget with launcher, open/close, minimize, quick questions, typing feedback, a new-chat control, a contact form, and a developer-only intent inspector. The admin workspace supports login, knowledge create/edit/delete, opt-in contact list, and protected chat history.
- A missing model or KB leaves the API in an unavailable state. A missing active intent answer leads to `clarify`. Explicit DIY hardware-repair requests use `KB-REPAIR`. These G4 product rules do not change the frozen G3 test results.
- No actual order, refund, account operation, shipment lookup, review publication, or human-agent connection occurs.

## User decisions applied

- Keep the old chatbot's widget and admin functions as the interaction model; write a new English storefront for Demo Tech Store.
- Use white and technology blue for the storefront, widget and admin workspace; use restrained motion with reduced-motion support.
- Save contact details only after a visitor submits the explicit consent form.
- Use friendly, concise KB responses while preserving the student-approved simulated policies. All 27 intent responses and four fallbacks were approved by the student on 28 October 2026; the wording no longer directs visitors to nonexistent order, account, invoice, or checkout screens.

## Chat UI polish

- Action tags use distinct, labeled colors for `guide`, `clarify`, `scope_boundary`, and `handoff`. Message text is 13px for video legibility.
- The chat header has an AI diagnostics toggle. Its probability and nearest-cosine bars use thresholds supplied by the API from the frozen G3 policy; the card explains that classifier probability is not an in-scope probability.
- A `clarify` reply offers three topic-aware, complete follow-up questions. The suggestions remain independent single-turn inputs, not simulated conversation memory. Suggestions are hidden when an active KB answer is missing.
- A browser check confirmed that a gaming-laptop order ambiguity produced `clarify`, and tapping “How can I change an item in my order?” produced a direct `guide` answer. Preview: `reports/g4/ui_polish_preview.png`.

## Verification

- Python tests cover guide, clarify, scope boundary, human handoff, DIY repair boundary, unavailable model, unauthenticated admin access, explicit contact consent, knowledge CRUD, local chat history, missing KB answer fallback, and persistence of knowledge deletion across restart.
- The React/Vite production build succeeds.
- A live local smoke run with the actual G3 model returned `KB-DELIVERY-PERIOD`, `KB-HUMAN-AGENT`, `KB-REPAIR` and `KB-SCOPE` for their respective prompts. An unauthenticated admin request returned HTTP 401.
- Browser inspection confirmed the storefront, chat startup, live KB reply, contact consent form, admin login, and loaded knowledge cards. An end-to-end contact form submission with disposable test details appeared in the admin contact list; the interface stated that no real team was notified.
- Visual previews: `reports/g4/storefront_preview.png`, `reports/g4/admin_preview.png`, and `reports/g4/contact_flow_preview.png`.

## Limits for G5/report

- The G3 challenge final action score was 13/22 and not fully blind, as disclosed in `reports/g3/final_report.md`. The demo deliberately retains clarification and scope fallbacks; it is not validated for real customer service.
- Contact and message records live only in the local SQLite file. No deletion-by-visitor flow or production data-retention policy is provided.
- Admin credentials come from environment variables. Tokens are server-memory only and expire after eight hours or on restart. The demo binds to localhost in the documented command and has no production deployment configuration.
- Source and design inheritance from the old chatbot are recorded in `docs/planning/CODE_REUSE_G4.md`.
