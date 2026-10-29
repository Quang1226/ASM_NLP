"""Small checks for material data leakage and reproducibility risks."""

import sys
import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from intent_support.data.bitext import normalize_instruction
from split_data import make_splits, prune_cross_split_near_duplicates, unique_examples


class DataPreparationTests(unittest.TestCase):
    def test_normalized_duplicates_stay_one_example(self):
        rows = [
            {"instruction": "Where is MY order?", "intent": "track_order"},
            {"instruction": " where is my  order? ", "intent": "track_order"},
        ]
        grouped = unique_examples(rows)
        self.assertEqual(len(grouped["track_order"]), 1)

    def test_conflicting_labels_fail_fast(self):
        rows = [
            {"instruction": "Where is my order?", "intent": "track_order"},
            {"instruction": "where is my order?", "intent": "cancel_order"},
        ]
        with self.assertRaises(ValueError):
            unique_examples(rows)

    def test_split_is_deterministic_and_disjoint(self):
        rows = [
            {"instruction": f"{hashlib.sha256(str(i).encode()).hexdigest()} {label}", "intent": label}
            for label in ("track_order", "cancel_order")
            for i in range(40)
        ]
        groups = unique_examples(rows)
        first, _ = make_splits(groups)
        second, _ = make_splits(groups)
        self.assertEqual(first, second)
        keys = [
            {normalize_instruction(row["instruction"]) for row in first[split]}
            for split in ("train", "validation", "test")
        ]
        self.assertFalse(keys[0] & keys[1] | keys[0] & keys[2] | keys[1] & keys[2])
        for examples in first.values():
            self.assertEqual(set(row["intent"] for row in examples), set(groups))

    def test_near_duplicates_form_one_group(self):
        from split_data import near_duplicate_groups

        examples = [
            {"instruction": "assistance to speak with a live agent", "intent": "contact_human_agent"},
            {"instruction": "assistance to speak to a live agent", "intent": "contact_human_agent"},
            {"instruction": "I want to create a new customer account", "intent": "contact_human_agent"},
        ]
        groups = near_duplicate_groups(examples)
        self.assertEqual(sorted(map(len, groups)), [1, 2])

    def test_strict_pruning_removes_cross_split_near_duplicates(self):
        splits = {
            "train": [{"instruction": "getting invoice #37777", "intent": "get_invoice"}],
            "validation": [{"instruction": "get invoice #37777", "intent": "get_invoice"}],
            "test": [
                {"instruction": "getting invoice #37777?", "intent": "get_invoice"},
                {"instruction": "What are your delivery options?", "intent": "delivery_options"},
            ],
        }
        clean, removed = prune_cross_split_near_duplicates(splits)
        self.assertEqual(clean["validation"], [])
        self.assertEqual(len(clean["test"]), 1)
        self.assertEqual(sum(removed.values()), 2)


if __name__ == "__main__":
    unittest.main()
