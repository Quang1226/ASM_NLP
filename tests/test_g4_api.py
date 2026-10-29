"""Exercise the actual API, local storage, protected admin routes and KB fallbacks."""

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from backend.main import Settings, create_app
from backend.store import DemoStore


class FakePredictor:
    def __init__(self, root):
        kb = json.loads((Path(root) / "data/kb/tech_store_kb.json").read_text())
        self.intents = {item["intent"] for item in kb["intent_responses"]}
        self.model_version = "test-frozen-bundle"
        self.policy = json.loads((Path(root) / "reports/g3/frozen_bundle.json").read_text())["policy"]

    def predict(self, text):
        if "weather" in text:
            intent, action = "delivery_period", "scope_boundary"
        elif "unclear" in text:
            intent, action = "change_order", "clarify"
        elif "human" in text:
            intent, action = "contact_human_agent", "handoff"
        else:
            intent, action = "track_order", "guide"
        return {"predicted_intent": intent, "confidence": 0.9,
                "nearest_train_cosine": 0.7, "action": action,
                "model_version": self.model_version}


def test_chat_routes_and_admin_privacy(tmp_path):
    settings = Settings(root=ROOT, db_path=tmp_path / "fresh_demo.sqlite",
                        admin_username="localadmin", admin_password="test-secret")
    with TestClient(create_app(settings, predictor_factory=FakePredictor)) as client:
        assert client.get("/api/health").json()["ready"] is True
        session = client.post("/api/chat/start").json()["session_id"]
        msg = client.post("/api/chat/message", json={"session_id": session, "message_text": "Track my demo order"})
        assert msg.status_code == 200
        assert msg.json()["kb_reference"] == "KB-TRACK-ORDER"
        assert msg.json()["simulated"] is True
        assert msg.json()["score_type"] == "classifier_probability_not_scope_probability"
        assert msg.json()["decision_thresholds"] == {
            "clarify_probability": 0.663174,
            "scope_similarity": 0.396708,
        }

        for text, action, ref in [
            ("This is unclear", "clarify", "KB-CLARIFY"),
            ("What is the weather?", "scope_boundary", "KB-SCOPE"),
            ("I want a human", "handoff", "KB-HUMAN-AGENT"),
            ("How do I repair my laptop screen myself?", "scope_boundary", "KB-REPAIR"),
        ]:
            reply = client.post("/api/chat/message", json={"session_id": session, "message_text": text})
            assert reply.status_code == 200
            assert (reply.json()["action_taken"], reply.json()["kb_reference"]) == (action, ref)

        assert client.post("/api/chat/message", json={"session_id": "0" * 36, "message_text": "hello"}).status_code == 404
        assert client.get("/api/admin/leads").status_code == 401
        assert client.get(f"/api/admin/history/{session}").status_code == 401
        assert client.get("/api/admin/knowledge").status_code == 401
        assert client.post("/api/admin/login", json={"username": "localadmin", "password": "wrong"}).status_code == 401
        assert client.post("/api/chat/contact", json={"session_id": session, "name": "A Demo Customer", "contact_value": "demo@example.com", "note": "Please follow up", "consent": False}).status_code == 422

        login = client.post("/api/admin/login", json={"username": "localadmin", "password": "test-secret"})
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        assert client.get("/api/admin/leads", headers=headers).json() == []
        contact = client.post("/api/chat/contact", json={"session_id": session, "name": "A Demo Customer", "contact_value": "demo@example.com", "note": "Please follow up", "consent": True})
        assert contact.status_code == 200
        leads = client.get("/api/admin/leads", headers=headers).json()
        assert len(leads) == 1 and leads[0]["contact_value"] == "demo@example.com"
        history = client.get(f"/api/admin/history/{session}", headers=headers).json()
        assert len(history) == 10
        assert all(item["message_text"] != "demo@example.com" for item in history)

        knowledge = client.get("/api/admin/knowledge", headers=headers).json()
        assert len(knowledge) == 27
        created = client.post("/api/admin/knowledge", headers=headers,
                              json={"intent": "track_order", "response": "Custom local demo tracking answer."})
        assert created.status_code == 200
        custom_id = created.json()["id"]
        reply = client.post("/api/chat/message", json={"session_id": session, "message_text": "Track my demo order"}).json()
        assert reply["kb_reference"].startswith("KB-CUSTOM-")
        assert client.put(f"/api/admin/knowledge/{custom_id}", headers=headers,
                          json={"response": "Updated answer.", "active": True}).status_code == 200
        assert client.post("/api/chat/message", json={"session_id": session, "message_text": "Track my demo order"}).json()["message_text"] == "Updated answer."
        assert client.delete(f"/api/admin/knowledge/{custom_id}", headers=headers).status_code == 200
        assert client.post("/api/chat/message", json={"session_id": session, "message_text": "Track my demo order"}).json()["kb_reference"] == "KB-TRACK-ORDER"
        seed_id = next(item["id"] for item in knowledge if item["intent"] == "track_order")
        assert client.delete(f"/api/admin/knowledge/{seed_id}", headers=headers).status_code == 200
        missing = client.post("/api/chat/message", json={"session_id": session, "message_text": "Track my demo order"}).json()
        assert (missing["action_taken"], missing["decision_reason"], missing["kb_reference"]) == (
            "clarify", "missing_active_kb_entry", "KB-CLARIFY")
        assert client.delete(f"/api/admin/leads/{leads[0]['id']}", headers=headers).status_code == 200
        assert client.get("/api/admin/leads", headers=headers).json() == []
        assert client.post("/api/admin/logout", headers=headers).status_code == 200
        assert client.get("/api/admin/knowledge", headers=headers).status_code == 401
    reopened = DemoStore(tmp_path / "fresh_demo.sqlite", ROOT / "data/kb/tech_store_kb.json")
    assert reopened.response_for_intent("track_order") is None


def test_missing_model_returns_clear_unavailable_state(tmp_path):
    class BrokenPredictor:
        def __init__(self, root):
            raise FileNotFoundError("missing model")

    settings = Settings(root=ROOT, db_path=tmp_path / "fresh_demo.sqlite")
    with TestClient(create_app(settings, predictor_factory=BrokenPredictor)) as client:
        assert client.get("/api/health").json()["ready"] is False
        response = client.post("/api/chat/start")
        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"]


def test_reviewed_seed_copy_refreshes_without_overwriting_admin_edits(tmp_path):
    source = json.loads((ROOT / "data/kb/tech_store_kb.json").read_text())
    kb_path = tmp_path / "reviewed_kb.json"
    kb_path.write_text(json.dumps(source), encoding="utf-8")
    db_path = tmp_path / "demo.sqlite"
    store = DemoStore(db_path, kb_path)
    seed = next(item for item in store.knowledge() if item["intent"] == "track_order")
    source["intent_responses"] = [
        {**item, "response": "New approved tracking copy."} if item["intent"] == "track_order" else item
        for item in source["intent_responses"]
    ]
    kb_path.write_text(json.dumps(source), encoding="utf-8")
    store = DemoStore(db_path, kb_path)
    assert store.response_for_intent("track_order")["response"] == "New approved tracking copy."
    assert store.update_knowledge(seed["id"], "My local admin wording.", True)
    source["intent_responses"] = [
        {**item, "response": "Another source revision."} if item["intent"] == "track_order" else item
        for item in source["intent_responses"]
    ]
    kb_path.write_text(json.dumps(source), encoding="utf-8")
    store = DemoStore(db_path, kb_path)
    assert store.response_for_intent("track_order")["response"] == "My local admin wording."
