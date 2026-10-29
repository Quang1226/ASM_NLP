# G2 validation comparison

All experiments use the frozen train/validation split, the same preprocessing configuration, unigram+bigrams, min_df=2, max_features=50,000, and C grid [0.1, 1.0, 10.0]. Vectorizers are fitted inside the pipeline on train only. Test and challenge-final are untouched.

## Best C per experiment

| Experiment | Representation | Classifier | C | Accuracy | Macro-P | Macro-R | Macro-F1 | Features |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| E1 | bow | logistic_regression | 10.0 | 0.9822 | 0.9809 | 0.9806 | 0.9805 | 3,714 |
| E2 | bow | linear_svm | 1.0 | 0.9840 | 0.9836 | 0.9824 | 0.9828 | 3,714 |
| E3 | tfidf | logistic_regression | 10.0 | 0.9857 | 0.9861 | 0.9836 | 0.9846 | 3,714 |
| E4 | tfidf | linear_svm | 1.0 | 0.9854 | 0.9858 | 0.9838 | 0.9846 | 3,714 |

## Controlled comparison at C=1

| Experiment | Macro-F1 | Accuracy |
| --- | ---: | ---: |
| E1 | 0.9798 | 0.9808 |
| E2 | 0.9828 | 0.9840 |
| E3 | 0.9780 | 0.9788 |
| E4 | 0.9846 | 0.9854 |

## Preprocessing ablation on the selected E1–E4 family

| Variant | Macro-F1 | Δ vs full | Accuracy |
| --- | ---: | ---: | ---: |
| full | 0.9846 | +0.0000 | 0.9857 |
| no_normalization | 0.9850 | +0.0004 | 0.9860 |
| whitespace_tokenizer | 0.9808 | -0.0038 | 0.9817 |
| no_lemmatization | 0.9829 | -0.0017 | 0.9845 |

The whitespace-tokenizer ablation replaces the custom regex/placeholder tokenizer with whitespace splitting; tokenization remains necessary for word features. The no-normalization ablation disables Unicode/case/whitespace/contraction normalization. No-lemma keeps tokenization but omits POS-aware WordNet lemmatization.

Fit durations include cache effects and are not a fair training-speed comparison. Inference latency and final test evaluation belong to G3.
