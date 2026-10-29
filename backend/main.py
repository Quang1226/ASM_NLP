"""FastAPI app for the local, simulated Demo Tech Store chatbot."""

from __future__ import annotations

import logging
import os
import re
import secrets
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from backend.service import ChatService, FrozenPredictor
from backend.store import DemoStore

ROOT = Path(__file__).resolve().parents[1]
LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Settings:
    root: Path = ROOT
    db_path: Path | None = None
    admin_username: str | None = None
    admin_password: str | None = None
    cors_origins: tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")

    @classmethod
    def from_env(cls) -> "Settings":
        root = Path(os.environ.get("DEMO_ROOT") or ROOT).resolve()
        db_path = Path(os.environ.get("DEMO_DB_PATH") or root / "data/demo/demo_store.sqlite").resolve()
        origins = tuple(x.strip() for x in os.environ.get(
            "DEMO_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if x.strip())
        return cls(root=root, db_path=db_path,
                   admin_username=os.environ.get("DEMO_ADMIN_USERNAME"),
                   admin_password=os.environ.get("DEMO_ADMIN_PASSWORD"), cors_origins=origins)


class ChatMessageIn(BaseModel):
    session_id: str = Field(min_length=36, max_length=36)
    message_text: str = Field(min_length=1, max_length=1000)

    @field_validator("message_text")
    @classmethod
    def nonempty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message cannot be blank")
        return value.strip()


class ContactIn(BaseModel):
    session_id: str = Field(min_length=36, max_length=36)
    name: str = Field(min_length=1, max_length=80)
    contact_value: str = Field(min_length=5, max_length=120)
    note: str = Field(default="", max_length=500)
    consent: bool

    @field_validator("name", "contact_value")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Field cannot be blank")
        return value.strip()

    @field_validator("contact_value")
    @classmethod
    def email_or_phone(cls, value: str) -> str:
        if "@" in value:
            if not re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", value):
                raise ValueError("Enter an email address or phone number")
        else:
            digits = re.sub(r"\D", "", value)
            if not re.fullmatch(r"\+?[0-9 ()-]+", value) or not 7 <= len(digits) <= 15:
                raise ValueError("Enter an email address or phone number")
        return value


class LoginIn(BaseModel):
    username: str
    password: str


class KnowledgeCreate(BaseModel):
    intent: str
    response: str = Field(min_length=1, max_length=2000)


class KnowledgeUpdate(BaseModel):
    response: str = Field(min_length=1, max_length=2000)
    active: bool = True


def create_app(settings: Settings | None = None, predictor_factory=FrozenPredictor) -> FastAPI:
    config = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.ready_error = None
        app.state.admin_tokens = {}
        try:
            store = DemoStore(config.db_path or config.root / "data/demo/demo_store.sqlite",
                              config.root / "data/kb/tech_store_kb.json")
            predictor = predictor_factory(config.root)
            service = ChatService(config.root, store, predictor)
            app.state.store = store
            app.state.service = service
        except Exception as exc:
            app.state.ready_error = type(exc).__name__
            LOGGER.exception("Demo initialization failed")
        yield
        app.state.admin_tokens.clear()

    app = FastAPI(title="Demo Tech Store API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=list(config.cors_origins),
                       allow_methods=["GET", "POST", "PUT", "DELETE"],
                       allow_headers=["Authorization", "Content-Type"], allow_credentials=False)

    def ready_store() -> DemoStore:
        if app.state.ready_error:
            raise HTTPException(status_code=503, detail="Demo model or knowledge base is unavailable")
        return app.state.store

    def ready_service() -> ChatService:
        if app.state.ready_error:
            raise HTTPException(status_code=503, detail="Demo model or knowledge base is unavailable")
        return app.state.service

    def require_admin(authorization: str | None = Header(default=None)) -> None:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Admin token required",
                                headers={"WWW-Authenticate": "Bearer"})
        token = authorization.removeprefix("Bearer ")
        expiry = app.state.admin_tokens.get(token)
        if expiry is None or expiry <= time.time():
            raise HTTPException(status_code=401, detail="Invalid or expired admin token",
                                headers={"WWW-Authenticate": "Bearer"})

    @app.get("/api/health")
    def health():
        if app.state.ready_error:
            return {"ready": False, "reason": "model_or_kb_unavailable"}
        return {"ready": True, "store": app.state.service.store_name,
                "model_version": app.state.service.predictor.model_version, "simulated": True}

    @app.post("/api/chat/start")
    def start_chat(store: DemoStore = Depends(ready_store)):
        return {"session_id": store.new_session(), "message": "Demo chat is ready.", "simulated": True}

    @app.post("/api/chat/message")
    def send_message(payload: ChatMessageIn, store: DemoStore = Depends(ready_store),
                     service: ChatService = Depends(ready_service)):
        if not store.has_session(payload.session_id):
            raise HTTPException(status_code=404, detail="Unknown chat session")
        reply = service.respond(payload.message_text)
        store.add_message(payload.session_id, "user", payload.message_text)
        store.add_message(payload.session_id, "bot", reply["message_text"],
                          reply["predicted_intent"], reply["action_taken"])
        return reply

    @app.post("/api/chat/contact")
    def leave_contact(payload: ContactIn, store: DemoStore = Depends(ready_store)):
        if not payload.consent:
            raise HTTPException(status_code=422, detail="Explicit contact consent is required")
        if not store.has_session(payload.session_id):
            raise HTTPException(status_code=404, detail="Unknown chat session")
        contact_id = store.add_contact(payload.session_id, payload.name,
                                       payload.contact_value, payload.note)
        return {"id": contact_id, "message": "Contact details were saved locally for this demo. No real support team was notified.",
                "simulated": True}

    @app.post("/api/admin/login")
    def admin_login(payload: LoginIn):
        if not config.admin_username or not config.admin_password:
            raise HTTPException(status_code=503, detail="Demo admin login is not configured")
        if not (secrets.compare_digest(payload.username, config.admin_username)
                and secrets.compare_digest(payload.password, config.admin_password)):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = secrets.token_urlsafe(32)
        app.state.admin_tokens[token] = time.time() + 8 * 3600
        return {"access_token": token, "token_type": "bearer", "expires_in": 8 * 3600}

    @app.post("/api/admin/logout", dependencies=[Depends(require_admin)])
    def admin_logout(authorization: str = Header()):
        app.state.admin_tokens.pop(authorization.removeprefix("Bearer "), None)
        return {"ok": True}

    @app.get("/api/admin/knowledge", dependencies=[Depends(require_admin)])
    def list_knowledge(store: DemoStore = Depends(ready_store)):
        return store.knowledge()

    @app.post("/api/admin/knowledge", dependencies=[Depends(require_admin)])
    def create_knowledge(payload: KnowledgeCreate, store: DemoStore = Depends(ready_store),
                         service: ChatService = Depends(ready_service)):
        if payload.intent not in service.predictor.intents:
            raise HTTPException(status_code=422, detail="Unknown trained intent")
        response = payload.response.strip()
        if not response:
            raise HTTPException(status_code=422, detail="Response cannot be blank")
        action_name = "handoff" if payload.intent == "contact_human_agent" else "guide"
        return store.add_knowledge(payload.intent, response, action_name, [])

    @app.put("/api/admin/knowledge/{item_id}", dependencies=[Depends(require_admin)])
    def update_knowledge(item_id: int, payload: KnowledgeUpdate,
                         store: DemoStore = Depends(ready_store)):
        if not payload.response.strip():
            raise HTTPException(status_code=422, detail="Response cannot be blank")
        if not store.update_knowledge(item_id, payload.response.strip(), payload.active):
            raise HTTPException(status_code=404, detail="Knowledge entry not found")
        return {"ok": True}

    @app.delete("/api/admin/knowledge/{item_id}", dependencies=[Depends(require_admin)])
    def delete_knowledge(item_id: int, store: DemoStore = Depends(ready_store)):
        if not store.delete_knowledge(item_id):
            raise HTTPException(status_code=404, detail="Knowledge entry not found")
        return {"ok": True}

    @app.get("/api/admin/leads", dependencies=[Depends(require_admin)])
    def leads(store: DemoStore = Depends(ready_store)):
        return store.contacts()

    @app.delete("/api/admin/leads/{contact_id}", dependencies=[Depends(require_admin)])
    def delete_lead(contact_id: int, store: DemoStore = Depends(ready_store)):
        if not store.delete_contact(contact_id):
            raise HTTPException(status_code=404, detail="Contact not found")
        return {"ok": True}

    @app.get("/api/admin/history/{session_id}", dependencies=[Depends(require_admin)])
    def history(session_id: str, store: DemoStore = Depends(ready_store)):
        if not store.has_session(session_id):
            raise HTTPException(status_code=404, detail="Unknown chat session")
        return store.conversation(session_id)

    @app.get("/api/admin/diagnostics", dependencies=[Depends(require_admin)])
    def diagnostics(store: DemoStore = Depends(ready_store), service: ChatService = Depends(ready_service)):
        return {"counts": store.counts(), "model_version": service.predictor.model_version,
                "knowledge_intent_count": len(service.predictor.intents), "simulated": True}

    return app


app = create_app()
