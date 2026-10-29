"""Fresh local SQLite state for the G4 demo; never imports the old VNJ database."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DemoStore:
    def __init__(self, path: Path, kb_path: Path):
        self.path = Path(path)
        self.kb_path = Path(kb_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def _initialize(self):
        kb = json.loads(self.kb_path.read_text(encoding="utf-8"))
        entries = kb["intent_responses"]
        if len(entries) != 27 or len({entry["intent"] for entry in entries}) != 27:
            raise ValueError("Knowledge base must cover all 27 unique intents")
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                    sender TEXT NOT NULL CHECK(sender IN ('user','bot')),
                    message_text TEXT NOT NULL,
                    intent TEXT,
                    action TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id,id);
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    contact_value TEXT NOT NULL,
                    note TEXT NOT NULL,
                    consent_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    intent TEXT NOT NULL,
                    kb_reference TEXT NOT NULL UNIQUE,
                    response TEXT NOT NULL,
                    action TEXT NOT NULL CHECK(action IN ('guide','handoff')),
                    policy_refs TEXT NOT NULL,
                    is_seed INTEGER NOT NULL DEFAULT 0,
                    edited INTEGER NOT NULL DEFAULT 0,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_knowledge_intent ON knowledge(intent,active,is_seed,id);
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY, value TEXT NOT NULL
                );
            """)
            # Existing local demo databases predate the reviewed KB wording.
            if "edited" not in {row["name"] for row in db.execute("PRAGMA table_info(knowledge)")}:
                db.execute("ALTER TABLE knowledge ADD COLUMN edited INTEGER NOT NULL DEFAULT 0")
            seeded = db.execute("SELECT 1 FROM meta WHERE key='kb_seeded'").fetchone()
            if not seeded:
                for entry in entries:
                    db.execute("""INSERT OR IGNORE INTO knowledge
                        (intent,kb_reference,response,action,policy_refs,is_seed,active,created_at)
                        VALUES (?,?,?,?,?,1,1,?)""",
                        (entry["intent"], entry["kb_reference"], entry["response"], entry["action"],
                         json.dumps(entry["policy_refs"]), now()))
                db.execute("INSERT INTO meta(key,value) VALUES ('kb_seeded','1')")
            # Source-managed seed rows receive approved copy on restart. Admin edits
            # made after this migration, custom answers, and deleted seeds survive.
            for entry in entries:
                db.execute("""UPDATE knowledge SET response=?,action=?,policy_refs=?
                    WHERE kb_reference=? AND is_seed=1 AND edited=0""",
                    (entry["response"], entry["action"], json.dumps(entry["policy_refs"]),
                     entry["kb_reference"]))

    def new_session(self) -> str:
        session_id = str(uuid.uuid4())
        with self._connect() as db:
            db.execute("INSERT INTO sessions(id,created_at) VALUES (?,?)", (session_id, now()))
        return session_id

    def has_session(self, session_id: str) -> bool:
        with self._connect() as db:
            return db.execute("SELECT 1 FROM sessions WHERE id=?", (session_id,)).fetchone() is not None

    def add_message(self, session_id: str, sender: str, text: str, intent: str | None = None,
                    action: str | None = None) -> None:
        with self._connect() as db:
            db.execute("""INSERT INTO messages(session_id,sender,message_text,intent,action,created_at)
                VALUES (?,?,?,?,?,?)""", (session_id, sender, text, intent, action, now()))

    def conversation(self, session_id: str) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("""SELECT id,sender,message_text,intent,action,created_at FROM messages
                WHERE session_id=? ORDER BY id""", (session_id,)).fetchall()
        return [dict(row) for row in rows]

    def add_contact(self, session_id: str, name: str, contact_value: str, note: str) -> int:
        with self._connect() as db:
            cursor = db.execute("""INSERT INTO contacts(session_id,name,contact_value,note,consent_at)
                VALUES (?,?,?,?,?)""", (session_id, name, contact_value, note, now()))
            return int(cursor.lastrowid)

    def contacts(self) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("""SELECT id,session_id,name,contact_value,note,consent_at
                FROM contacts ORDER BY id DESC""").fetchall()
        return [dict(row) for row in rows]

    def delete_contact(self, contact_id: int) -> bool:
        with self._connect() as db:
            cursor = db.execute("DELETE FROM contacts WHERE id=?", (contact_id,))
            return cursor.rowcount > 0

    def knowledge(self) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("""SELECT id,intent,kb_reference,response,action,policy_refs,is_seed,active
                FROM knowledge ORDER BY intent,is_seed DESC,id""").fetchall()
        return [{**dict(row), "policy_refs": json.loads(row["policy_refs"]),
                 "is_seed": bool(row["is_seed"]), "active": bool(row["active"])} for row in rows]

    def response_for_intent(self, intent: str) -> dict | None:
        with self._connect() as db:
            row = db.execute("""SELECT kb_reference,response,action FROM knowledge
                WHERE intent=? AND active=1 ORDER BY is_seed ASC,id DESC LIMIT 1""", (intent,)).fetchone()
        return dict(row) if row else None

    def add_knowledge(self, intent: str, response: str, action: str, policy_refs: list[str]) -> dict:
        ref = f"KB-CUSTOM-{uuid.uuid4().hex[:12].upper()}"
        with self._connect() as db:
            cursor = db.execute("""INSERT INTO knowledge(intent,kb_reference,response,action,policy_refs,is_seed,active,created_at)
                VALUES (?,?,?,?,?,0,1,?)""", (intent, ref, response, action, json.dumps(policy_refs), now()))
            item_id = int(cursor.lastrowid)
        return {"id": item_id, "intent": intent, "kb_reference": ref, "response": response,
                "action": action, "policy_refs": policy_refs, "is_seed": False, "active": True}

    def update_knowledge(self, item_id: int, response: str, active: bool) -> bool:
        with self._connect() as db:
            cursor = db.execute("UPDATE knowledge SET response=?,active=?,edited=1 WHERE id=?",
                                (response, int(active), item_id))
            return cursor.rowcount > 0

    def delete_knowledge(self, item_id: int) -> bool:
        with self._connect() as db:
            cursor = db.execute("DELETE FROM knowledge WHERE id=?", (item_id,))
            return cursor.rowcount > 0

    def counts(self) -> dict[str, int]:
        with self._connect() as db:
            return {table: int(db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                    for table in ("sessions", "messages", "contacts", "knowledge")}
