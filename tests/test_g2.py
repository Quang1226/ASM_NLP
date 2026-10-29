"""Check negation handling, explicit tokenization, and train-only vocabulary fit."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from intent_support.experiments.g2 import build_pipeline
from intent_support.preprocessing.text import TextPreprocessor, normalize_text


class G2Tests(unittest.TestCase):
    def test_normalization_and_lemmatization_keep_negation(self):
        self.assertEqual(normalize_text("I can’t cancel  my order"), "i can not cancel my order")
        tokens = TextPreprocessor().fit_transform(["I did not receive my orders"])[0]
        self.assertIn("not", tokens)
        self.assertIn("receive", tokens)
        self.assertIn("order", tokens)

    def test_regex_tokenizer_recognizes_slots(self):
        tokens = TextPreprocessor(lemmatize=False).fit_transform(["Track {{Order Number}} now"])[0]
        self.assertEqual(tokens, ["track", "slot_order_number", "now"])

    def test_vectorizer_learns_vocabulary_from_train_only(self):
        train = [
            "track my blue order", "track the blue package", "where is my blue order",
            "cancel my red order", "cancel the red package", "stop my red order",
        ]
        labels = ["track_order"] * 3 + ["cancel_order"] * 3
        pipeline = build_pipeline("bow", "logistic_regression", 1.0, preprocess={"normalize": True, "tokenizer": "regex", "lemmatize": False})
        pipeline.fit(train, labels)
        pipeline.predict(["track my quasar order"])
        vocabulary = pipeline.named_steps["features"].vocabulary_
        self.assertIn("blue", vocabulary)
        self.assertNotIn("quasar", vocabulary)


if __name__ == "__main__":
    unittest.main()
