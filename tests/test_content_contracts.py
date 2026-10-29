"""Keep challenge labels and demo knowledge aligned with the audited dataset."""

import csv
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ContentContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.intents = set(json.loads((ROOT / "reports" / "data_audit.json").read_text())["intents"])
        cls.kb = json.loads((ROOT / "data" / "kb" / "tech_store_kb.json").read_text())
        with (ROOT / "data" / "challenge" / "challenge_draft.csv").open(newline="", encoding="utf-8") as stream:
            cls.challenge = list(csv.DictReader(stream))

    def test_kb_covers_each_intent_once_with_valid_references(self):
        self.assertEqual(self.kb["store"]["intent_response_review_status"],
                         "approved_by_student_2026-10-28")
        self.assertEqual(self.kb["store"]["fallback_review_status"],
                         "approved_by_student_2026-10-28")
        self.assertEqual(len(self.kb["fallbacks"]), 4)
        entries = self.kb["intent_responses"]
        labels = [entry["intent"] for entry in entries]
        self.assertEqual(len(labels), len(set(labels)))
        self.assertEqual(set(labels), self.intents)
        policy_refs = {policy["reference"] for policy in self.kb["policies"].values()}
        kb_refs = [entry["kb_reference"] for entry in entries]
        self.assertEqual(len(kb_refs), len(set(kb_refs)))
        for entry in entries:
            self.assertTrue(entry["response"].strip())
            self.assertTrue(set(entry["policy_refs"]) <= policy_refs)

    def test_approved_challenge_covers_all_intents_and_matches_manifest(self):
        labels = {row["expected_intent"] for row in self.challenge if row["expected_intent"]}
        self.assertEqual(labels, self.intents)
        self.assertEqual(len(self.challenge), 44)
        self.assertEqual({row["partition"] for row in self.challenge}, {"tuning", "final"})
        self.assertTrue(all(row["review_status"] == "approved" for row in self.challenge))
        manifest = json.loads((ROOT / "data" / "challenge" / "challenge_manifest.json").read_text())
        actual = hashlib.sha256((ROOT / "data" / "challenge" / "challenge_draft.csv").read_bytes()).hexdigest()
        self.assertEqual(actual, manifest["sha256"])


if __name__ == "__main__":
    unittest.main()
