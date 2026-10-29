# Bitext data audit

- Rows: **26,872**
- Intents: **27**; categories: **11**
- Unique normalized instructions: **24,072**
- Duplicate rows after normalization: **2,800**
- Conflicting intent groups: **0**
- Missing values: **{'flags': 0, 'instruction': 0, 'category': 0, 'intent': 0, 'response': 0}**

## Intent counts

| Intent | Rows |
| --- | ---: |
| cancel_order | 998 |
| change_order | 997 |
| change_shipping_address | 973 |
| check_cancellation_fee | 950 |
| check_invoice | 1000 |
| check_payment_methods | 999 |
| check_refund_policy | 997 |
| complaint | 1000 |
| contact_customer_service | 1000 |
| contact_human_agent | 999 |
| create_account | 997 |
| delete_account | 995 |
| delivery_options | 995 |
| delivery_period | 999 |
| edit_account | 1000 |
| get_invoice | 999 |
| get_refund | 997 |
| newsletter_subscription | 999 |
| payment_issue | 999 |
| place_order | 998 |
| recover_password | 995 |
| registration_problems | 999 |
| review | 997 |
| set_up_shipping_address | 997 |
| switch_account | 1000 |
| track_order | 995 |
| track_refund | 998 |

## Category counts

| Category | Rows |
| --- | ---: |
| ACCOUNT | 5986 |
| CANCEL | 950 |
| CONTACT | 1999 |
| DELIVERY | 1994 |
| FEEDBACK | 1997 |
| INVOICE | 1999 |
| ORDER | 3988 |
| PAYMENT | 1998 |
| REFUND | 2992 |
| SHIPPING | 1970 |
| SUBSCRIPTION | 999 |

## Example customer requests

- `cancel_order`: question about cancelling order {{Order Number}}
- `delivery_period`: can you help me check how oson can I expect the parcel?
- `track_refund`: I need to know if there is anything new on the restitution

## Caveat

- This audit detects matches after Unicode/case/punctuation/whitespace normalization; it does not yet prove that generated paraphrase templates are isolated across splits.
- The dataset is hybrid synthetic, so performance on it does not establish production reliability.

## Post-split summary

- Deduplicated instructions before splitting: **24,072**; removed from raw data: **2,800**.
- Final split: train **16,849**, validation **3,491**, test **3,447**.
- `cancel_order`: **998** raw rows -> **421** unique normalized instructions -> **420** retained rows (train 295, validation 62, test 63). This class is much smaller than most others after deduplication.
- Invoice examples reuse only **4** literal numbers: #00108, #12588, #37777, #85632. This is a synthetic-template limitation.
- Additional near-duplicate holdout rows excluded: **285**; details in `split_report.json`.
- Residual cross-split matches at the reported similarity threshold: train_to_validation 0, train_to_test 0, validation_to_test 0.

The split and similarity analysis remain separate from model selection; the test set has not been used for training or tuning.
