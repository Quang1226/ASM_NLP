# G4 code reuse record

The old repository at `/Users/duyquang/Documents/CHATBOT-SERVICE` was inspected on 28 October 2026. No Python, JSX, CSS, database, secret, or static asset was copied into `NLP_ASM`. The new implementation was written for the approved English Demo Tech Store scope.

| Old source inspected | Behavior retained in the new demo | Replacement in NLP_ASM |
| --- | --- | --- |
| `vnj-chatbot-fe/src/components/ChatWidget/index.jsx` and `ChatWindow/*` | Floating launcher, open/close, minimize, chat messages and input | `frontend/src/App.jsx`, `frontend/src/styles.css` |
| `vnj-chatbot-fe/src/pages/Admin/AdminLogin.jsx` | Separate admin sign-in page | `frontend/src/AdminPage.jsx`, `/api/admin/login` |
| `vnj-chatbot-fe/src/pages/Admin/AdminDashboard.jsx` | Knowledge management, contact list and conversation history | `frontend/src/AdminPage.jsx`, protected `/api/admin/*` routes |
| `vnj-chatbot-fe/src/services/api.js` | Frontend API wrapper | `frontend/src/api.js` using native `fetch` |
| `vnj-chatbot-fe/package-lock.json` | Cached React/Vite dependency resolution as an offline installation starting point | `frontend/package-lock.json`, regenerated after removing unused packages and renaming the project |
| `app/main.py` and `app/api/v1/endpoints/chat.py` | FastAPI application and chat endpoints | `backend/main.py`, `backend/service.py`, `backend/store.py` |

The old `chatbot_vnj.db`, VNJ FAQ text, Groq prompt/API client, default admin account, automatic phone/email extraction, and unprotected lead/history endpoints were deliberately excluded. G4 uses a fresh local SQLite database, the frozen G3 classifier, and the student-reviewed simulated store policies. Contact records are created only when a visitor submits the explicit consent form. The admin token is created on successful login, kept in memory on the server, and held only in browser `sessionStorage`.

The 27 intent responses and four fallback wordings in `data/kb/tech_store_kb.json` were approved by the student on 28 October 2026. The replies distinguish the simulated policy from UI features that do not exist in the demo. Source-managed seed responses refresh on API restart; later admin edits and custom answers remain local to SQLite. This KB approval does not change the frozen model or G3 evaluation.
