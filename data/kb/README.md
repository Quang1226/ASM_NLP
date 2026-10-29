# Simulated technology store knowledge base

`tech_store_kb.json` is an English knowledge base for the fictional **Demo Tech Store**. The student approved the store name and simulated delivery, cancellation, refund, warranty and account rules on 28 October 2026. The 27 intent-specific response wordings remain a draft for review during demo integration. These rules are not Bitext `response` values or a real company's terms.

Every one of the 27 Bitext intent labels has a stable `kb_reference`, action and response. Global fallbacks cover clarification, human handoff, out-of-scope requests and DIY hardware repair. The chatbot must not claim to have changed an order, processed a payment, issued a refund, accessed an account or connected a live agent.

The DIY hardware-repair boundary is intentional: a request for self-repair instructions, such as replacing a laptop screen, receives `KB-REPAIR` and can be redirected to qualified service. Ordinary warranty or service-routing questions can be answered from `POL-WARRANTY` when the product flow supports them.
