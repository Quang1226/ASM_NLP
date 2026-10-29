# G2 methodology and interpretation

## Data boundary

The source is the pinned Bitext snapshot. G2 reads only `data/processed/train.csv` and `validation.csv`, verifies their hashes against `reports/split_report.json`, and uses only `instruction` as input and `intent` as the target. The test split and challenge `final` partition are reserved for G3.

## Three preprocessing techniques

1. **Normalization:** Unicode NFKC, apostrophe normalization, case folding, whitespace cleanup, and expansion of common negative contractions (`don't` → `do not`, `can't` → `can not`). This reduces superficial spelling variation and makes negation explicit.
2. **Tokenization:** a regex extracts words, numbers and Bitext placeholders. A placeholder such as `{{Order Number}}` becomes `slot_order_number`, avoiding separate brace fragments. The ablation substitutes whitespace splitting to measure this tokenizer's effect.
3. **POS-aware lemmatization:** the NLTK English POS tagger provides parts of speech to the WordNet lemmatizer (for example, `shipped` → `ship`). Negation words `not`, `no`, `never` and `cannot` are protected. Stop-word removal is deliberately omitted because it could remove negation or other short intent cues.

NLTK's [WordNet lemmatizer](https://www.nltk.org/api/nltk.stem.wordnet.html) and [data packages](https://www.nltk.org/data.html) are external pretrained linguistic resources, not additional classifiers trained for this assignment. The project downloads only WordNet and the English POS tagger, verifies their published SHA-256 values, and stores them outside Git.

## Controlled model comparison

- E1: BoW + Logistic Regression; E2: BoW + Linear SVM; E3: TF-IDF + Logistic Regression; E4: TF-IDF + Linear SVM.
- All use one `sklearn.Pipeline`: text preprocessor → vectorizer → classifier. The vectorizer learns vocabulary and IDF (TF-IDF only) from train; validation is transformed using the fitted pipeline.
- Both representations use word unigrams and bigrams, `min_df=2`, at most 50,000 features. Both classifiers search the same C values: 0.1, 1 and 10. The winner for each E-code is chosen by validation macro-F1, then accuracy, then smaller C on a tie.
- `reports/g2/candidate_results.csv` contains all 12 configurations. The comparison at fixed C=1 separates representation/model effects from the effect of choosing different C values. `best_by_experiment.json` stores the tuned comparison.
- Macro-F1 weights each of the 27 intents equally, which matters because `cancel_order` has fewer retained examples after deduplication. Accuracy and macro precision/recall are supplementary. Per-class scores and full confusion matrices are saved for each E-code.

## Findings on validation

E3 reaches macro-F1 **0.984594** and E4 **0.984585**; the difference is **0.000009**, so G2 does not establish a meaningful advantage for either. E3 is the provisional choice under the prespecified selection rule. The weakest E3 classes include `cancel_order` (F1 ≈ 0.941), `track_order` (≈ 0.961), `get_invoice` (≈ 0.963) and `check_invoice` (≈ 0.964). The most common confusion is `get_invoice` → `check_invoice` (9 validation cases).

On E3 with C=10, the normalization ablation changes macro-F1 by +0.000414, whitespace tokenization by −0.003831, and no lemmatization by −0.001672. These are observations on one validation split, not general claims that any step always helps. The tokenizer difference is the clearest in this run; normalization's effect is too small to interpret confidently.

The high scores are from a hybrid synthetic dataset with repeated patterns. Strict splitting removed same-intent string matches at `SequenceMatcher ≥ 0.90`, but lower-similarity paraphrases and template relationships may remain. Challenge-set robustness, decision thresholds, latency and final test evaluation are G3 work.
