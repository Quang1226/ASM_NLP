# Validation error analysis — G2

Selected among E1–E4: **E3**, C=10.0, macro-F1=0.9846.

This is an initial qualitative pass on validation only. Do not use the test split for model changes.

| True intent | Predicted intent | Count |
| --- | --- | ---: |
| get_invoice | check_invoice | 9 |
| track_order | change_order | 4 |
| change_order | place_order | 3 |
| check_refund_policy | check_cancellation_fee | 3 |
| create_account | registration_problems | 3 |
| cancel_order | delete_account | 2 |
| cancel_order | place_order | 2 |
| contact_customer_service | contact_human_agent | 2 |
| delete_account | switch_account | 2 |
| payment_issue | check_payment_methods | 2 |

## Representative mistakes

### get_invoice → check_invoice (9)

- downlpoad bills from {{Person Name}}
- i cannot find bill #85632 can usendit to me
- I want to downlpad my invoice from {{Person Name}}, I need help

### track_order → change_order (4)

- need to trafk order {{Order Number}} help me
- can uhelp melocate order {{Order Number}}
- when will I receive ordered {{Order Number}}?

### change_order → place_order (3)

- i want help to swap several articles of order113542617735902
- need help with switching some articles of an order
- hep changing some products of an order

### check_refund_policy → check_cancellation_fee (3)

- are the charges of your services refundable?
- are the service charges refundable?
- are service charges reimbursable?

### create_account → registration_problems (3)

- create user
- register
- creating user
