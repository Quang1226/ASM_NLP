# G3 final evaluation and model decision

Frozen bundle SHA-256: `fb3a88dfbbed4f90ce004f1c5b07470da28ea6ef9df8ab47c60f6978fb1bc17e`. Test and challenge final were evaluated after threshold selection; neither was used for model selection. During initial schema inspection, however, a command displayed the entire challenge CSV, including `final` rows, before freeze. The scoring code did not use those rows for selection, but the challenge-final result is **not fully blind** and should be treated as exploratory. The Bitext test split was not inspected before freeze.

## Validation comparison

| Model | Macro-F1 | Accuracy |
| --- | ---: | ---: |
| E3 | 0.984594 | 0.985677 |
| E4 | 0.984585 | 0.985391 |
| E5 | 0.989829 | 0.990261 |

E5 (frozen all-MiniLM-L6-v2 embeddings + Logistic Regression) was selected by validation macro-F1. E3 and E4 remain useful light baselines. High scores on synthetic Bitext do not establish real-world accuracy.

## Held-out Bitext test

3447 cases; accuracy 0.988106; macro precision 0.987943; macro recall 0.984357; macro-F1 0.985686.

## Challenge final

In-scope intent: 11/14; action: 13/22.

| Expected action | Correct | Total |
| --- | ---: | ---: |
| clarify | 2 | 4 |
| guide | 8 | 14 |
| scope_boundary | 3 | 4 |

The 22-case final partition is too small to estimate deployment OOS performance. The probability score is a classifier output, not a calibrated probability of being in scope. The cosine boundary was tuned on only four OOS examples; broader human-reviewed OOS coverage is needed before relying on automatic scope decisions.

The user chose the conservative policy before final evaluation. On challenge `tuning`, it routed all four ambiguous and all four OOS cases correctly but clarified nine of thirteen valid guide requests. On `final`, six of fourteen valid guide requests were clarified, two of four ambiguous requests received a guide action, and one of four OOS requests was clarified rather than sent to the scope boundary. One high-confidence in-scope error, F03, ignored the negation in "not trying to cancel" and predicted `cancel_order`; the action was `guide` but the KB answer would be wrong. F14 and F15 show that high classifier probability alone cannot guarantee an unambiguous request. These are concrete G4 fallback and UX risks, not reasons to retune on `final`.

## Latency on this machine

Apple Silicon CPU (`arm64`; MPS unavailable in this environment), `OPENBLAS_NUM_THREADS=4`, single message, 5 warm-up queries and 50 measured validation queries. Model load 0.449 s; median 8.382 ms; p95 9.500 ms. Timed path: encoder + classifier + full-train cosine search + decision (not model load). The local runtime also needs the ~91 MB encoder weights and 25.9 MB float32 training embedding bank; the small classifier itself is 81.5 KB.

## Frequent test confusions

| True | Predicted | Count |
| --- | --- | ---: |
| cancel_order | change_order | 12 |
| check_refund_policy | get_refund | 4 |
| check_invoice | get_invoice | 3 |
| track_order | change_order | 3 |
| track_order | delivery_period | 3 |
| change_order | place_order | 2 |
| registration_problems | create_account | 2 |
| change_order | cancel_order | 1 |
| change_shipping_address | contact_human_agent | 1 |
| check_refund_policy | track_refund | 1 |

## Representative mistakes

- `cancel_order` → `change_order`: i cannot poay for purchase {{Order Number}}
- `check_refund_policy` → `get_refund`: wanna see ur money back poolicy how do i do it
- `check_invoice` → `get_invoice`: I'm trying to fgind my bills from {{Person Name}}
- `track_order` → `change_order`: trackorder {{Order Number}}
- `track_order` → `delivery_period`: i dont know how i can check the eta of my last delivery
- `change_order` → `place_order`: I want to add a product to my order, could I get some help?
- `registration_problems` → `create_account`: question about opening user profiles
- `change_order` → `cancel_order`: chnaging order {{Order Number}}

## Decision for G4

Use frozen E5 for intent prediction. Keep safe `clarify`/`scope_boundary` fallbacks visible in the demo and do not claim these thresholds generalize beyond the small challenge set. KB answers are separate from Bitext responses. The encoder revision is pinned in the bundle and downloaded separately during setup.
