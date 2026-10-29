"""Deterministic predict -> decide -> retrieve -> respond demo pipeline."""

from __future__ import annotations

import json
import re
from pathlib import Path

import joblib
import numpy as np

from intent_support.data.bitext import sha256_file
from intent_support.experiments.g3_embedding import load_encoder
from intent_support.experiments.g3_policy import action, nearest_similarity

from backend.store import DemoStore


REPAIR_VERB = re.compile(r"\b(repair|replace|open|disassemble|take apart|fix)\b", re.I)
SELF_REPAIR = re.compile(r"\b(myself|yourself|diy|do[- ]it[- ]yourself|on my own|step[- ]by[- ]step)\b", re.I)
HARDWARE = re.compile(r"\b(laptop|screen|battery|motherboard|graphics card|gpu|ssd|hardware)\b", re.I)


def is_self_repair_request(text: str) -> bool:
    return bool(REPAIR_VERB.search(text) and SELF_REPAIR.search(text) and HARDWARE.search(text))


class FrozenPredictor:
    def __init__(self, root: Path):
        self.root = Path(root)
        freeze_path = self.root / "reports/g3/frozen_bundle.json"
        final_path = self.root / "reports/g3/final_evaluation.json"
        if not freeze_path.exists() or not final_path.exists():
            raise FileNotFoundError("G3 frozen bundle and evaluation are required")
        final = json.loads(final_path.read_text(encoding="utf-8"))
        if sha256_file(freeze_path) != final["frozen_bundle_sha256"]:
            raise ValueError("Frozen bundle hash differs from final evaluation")
        bundle = json.loads(freeze_path.read_text(encoding="utf-8"))
        model_path = self.root / bundle["classifier"]["model_file"]
        bank_path = self.root / bundle["train_embedding"]["file"]
        if sha256_file(model_path) != bundle["classifier"]["model_sha256"]:
            raise ValueError("G3 classifier hash mismatch")
        if sha256_file(bank_path) != bundle["train_embedding"]["file_sha256"]:
            raise ValueError("G3 embedding-bank hash mismatch")
        self.encoder = load_encoder()
        self.model = joblib.load(model_path)
        self.bank = np.load(bank_path, allow_pickle=False)
        if self.bank.shape != (bundle["train_embedding"]["rows"], bundle["train_embedding"]["dimensions"]):
            raise ValueError("G3 embedding-bank shape mismatch")
        self.policy = bundle["policy"]
        self.model_version = bundle["bundle_version"]
        self.intents = set(self.model.classes_.tolist())

    def predict(self, text: str) -> dict:
        vector = self.encoder.encode([text], normalize_embeddings=True, show_progress_bar=False)
        probabilities = self.model.predict_proba(vector)[0]
        winner = int(probabilities.argmax())
        intent = str(self.model.classes_[winner])
        confidence = float(probabilities[winner])
        nearest = float(nearest_similarity(vector, self.bank)[0])
        route = action(intent, confidence, nearest, text,
                       self.policy["scope_similarity_threshold"], self.policy["clarify_probability_threshold"])
        return {"predicted_intent": intent, "confidence": confidence,
                "nearest_train_cosine": nearest, "action": route,
                "model_version": self.model_version}


class ChatService:
    def __init__(self, root: Path, store: DemoStore, predictor: FrozenPredictor):
        self.root = Path(root)
        self.store = store
        self.predictor = predictor
        kb = json.loads((self.root / "data/kb/tech_store_kb.json").read_text(encoding="utf-8"))
        if kb["store"]["name"] != "Demo Tech Store":
            raise ValueError("Wrong knowledge base")
        self.fallbacks = kb["fallbacks"]
        if {entry["intent"] for entry in kb["intent_responses"]} != predictor.intents:
            raise ValueError("Model labels and knowledge-base intents differ")
        self.store_name = kb["store"]["name"]
        self.disclosure = kb["store"]["disclosure"]

    def respond(self, text: str) -> dict:
        prediction = self.predictor.predict(text)
        selected_action = prediction["action"]
        reason = "frozen_g3_policy"
        if is_self_repair_request(text):
            selected_action = "scope_boundary"
            fallback_key = "hardware_repair_boundary"
            reason = "hardware_self_repair_boundary"
        elif selected_action == "handoff":
            fallback_key = None
        elif selected_action in self.fallbacks:
            fallback_key = selected_action
        else:
            fallback_key = None
        if fallback_key is not None:
            entry = self.fallbacks[fallback_key]
        elif selected_action == "handoff":
            entry = self.store.response_for_intent("contact_human_agent") or self.fallbacks["handoff"]
        else:
            entry = self.store.response_for_intent(prediction["predicted_intent"])
            if entry is None:
                entry = self.fallbacks["clarify"]
                selected_action = "clarify"
                reason = "missing_active_kb_entry"
        return {"message_text": entry["response"],
                "predicted_intent": prediction["predicted_intent"],
                "score": round(prediction["confidence"], 6),
                "score_type": "classifier_probability_not_scope_probability",
                "nearest_train_cosine": round(prediction["nearest_train_cosine"], 6),
                "decision_thresholds": {
                    "clarify_probability": self.predictor.policy["clarify_probability_threshold"],
                    "scope_similarity": self.predictor.policy["scope_similarity_threshold"],
                } if hasattr(self.predictor, "policy") else None,
                "model_version": prediction["model_version"],
                "action_taken": selected_action,
                "decision_reason": reason,
                "kb_reference": entry["kb_reference"],
                "simulated": True}
