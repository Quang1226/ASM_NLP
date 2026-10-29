"""Check held-out boundaries and decision behavior without opening final data."""

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from intent_support.experiments.g3_policy import action, challenge_rows, nearest_similarity
from intent_support.experiments.g3_final import run as evaluate_final


class G3Tests(unittest.TestCase):
    def test_tuning_loader_returns_only_approved_tuning_rows(self):
        rows, manifest = challenge_rows(ROOT, "tuning")
        self.assertEqual(len(rows), 22)
        self.assertTrue(all(row["id"].startswith("T") for row in rows))
        self.assertEqual(manifest["status"], "approved_by_student_before_model_training")

    def test_scope_check_precedes_handoff_or_high_classifier_confidence(self):
        self.assertEqual(action("contact_human_agent", 0.99, 0.20, "Talk to a human agent",
                                0.40, 0.60), "scope_boundary")
        self.assertEqual(action("contact_customer_service", 0.20, 0.80, "I need a real support person",
                                0.40, 0.60), "handoff")

    def test_nearest_search_returns_full_bank_cosine_maximum(self):
        bank = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]], dtype=np.float32)
        query = np.array([[0.6, 0.8]], dtype=np.float32)
        self.assertAlmostEqual(float(nearest_similarity(query, bank, batch_size=1)[0]), 0.8, places=6)

    def test_final_evaluation_requires_preexisting_freeze(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                evaluate_final(Path(tmp))


if __name__ == "__main__":
    unittest.main()
