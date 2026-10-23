# Step 1 - FastAPI hello (`main.py`)

## What we did

- Created `agent-lab/backend/requirements.txt` with `fastapi` and `uvicorn[standard]`
- Created `agent-lab/backend/app/__init__.py` (empty)
- Created `agent-lab/backend/app/main.py` with `FastAPI(title="agent lab")` and a `GET /health` route returning `{"status": "ok"}`
- Created the venv, installed the requirements and ran the app with uvicorn

## Commands

```bash
cd agent-lab/backend
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Output

http://127.0.0.1:8000/health

```json
{"status": "ok"}
```

# Step 2 - Settings (`config.py`)

## Goal

One place for app config, same idea as production config files.

## Why this step

- Hardcoding `title="agent lab"` in `main.py` does not scale.
- Production applications load environment and DB settings into a singleton settings object that every module imports.
- We do the same pattern with two fields.

## What we did

- Added `pydantic-settings` to `agent-lab/backend/requirements.txt` (read environment variables into a typed settings class)
- Created `agent-lab/backend/app/config.py` with a `Settings` class (`BaseSettings`) with `app_name: str = "agent lab"` and `debug: bool = True`, and a single `settings = Settings()` instance
- Updated `agent-lab/backend/app/main.py` to import `settings` from `app.config`, use `FastAPI(title=settings.app_name)`, and return `app` and `debug` from `GET /health`
- Installed the requirements again and ran the app with uvicorn

## Commands

```bash
cd agent-lab/backend
source .venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Output

http://127.0.0.1:8000/health

```json
{"status": "ok", "app": "agent lab", "debug": true}
```

# Step 3 - Database (`database.py`)

## Goal

Connect to a database and give routes a session via `get_db()`, same pattern as production `database.py`.

## Why this step

- Chat, agent, users all need durable storage.
- FastAPI handlers should not open or close DB connections ad hoc.
- We centralize:
  - `engine`: connection pool to the DB
  - `SessionLocal`: factory for DB sessions (a session is a unit of work)
  - `Base`: parent class for ORM models (our next step)
  - `get_db()`: FastAPI dependency that yields a session and always closes it

## Note

- In production we use Postgres.
- Here we use SQLite to keep setup easy.

# Step 4 - First model (Conversation)

## Goal

Define a database table as a Python class and create it in SQLite.

## Why this step

- `database.py` only sets up the connection.
- A model is a Python class that maps to a SQL table.
- We start with one table, `Conversation` (a chat thread). Message comes in a later step.

## What we did

- Created `agent-lab/backend/app/models.py` with a `Conversation` model (`Base`) and table name `conversation`
  - `id`: `Column(Integer, primary_key=True, index=True)`
  - `title`: `Column(String, default="new chat")`
  - `created_at`: `Column(DateTime, default=lambda: datetime.now(timezone.utc))`
- Updated `agent-lab/backend/app/main.py` to import `models` (registers the model on `Base`) and call `Base.metadata.create_all(bind=engine)`, so the table is created when the app starts
- Ran the app with uvicorn; SQLite created `agent_lab.db` with the `conversation` table

## Commands

```bash
cd agent-lab/backend
source .venv/Scripts/activate
uvicorn app.main:app --reload --port 8000
```

## Output

http://127.0.0.1:8000/health

```json
{"status": "ok", "app": "agent lab", "debug": true}
```

Table `conversation` in `agent_lab.db`:

| column | type |
|---|---|
| id | INTEGER |
| title | VARCHAR |
| created_at | DATETIME |

# Step 5 - Router (create and list conversation)

## Goal

HTTP API to create and list conversations.

## Notes

- The router is the HTTP layer: it uses `get_db` and talks to the model.
- `main.py` should stay thin.
- Feature routes live in `routers/`, then get mounted with `include_router`.

## What we did

- Created `agent-lab/backend/app/routers/` with an empty `__init__.py`
- Created `agent-lab/backend/app/routers/conversations.py`:
  - `router = APIRouter(prefix="/api/conversations", tags=["conversations"])`
  - `ConversationCreate` (request body): `title: str = "new chat"`
  - `ConversationOut` (response): `id: int`, `title: str`, with `from_attributes = True` so it reads from the ORM model
  - `POST /api/conversations` (`create_conversation`): uses `get_db`, adds a `Conversation` row, commits, refreshes and returns it
  - `GET /api/conversations` (`list_conversations`): uses `get_db` and returns all conversations, newest first (`order_by(Conversation.id.desc())`)
- Updated `agent-lab/backend/app/main.py` to mount the router with `app.include_router(conversations.router)`; `/health` and `create_all` are unchanged, so `main.py` stays thin
- Ran the app with uvicorn and tested create and list with curl

## Commands

```bash
cd agent-lab/backend
source .venv/Scripts/activate
uvicorn app.main:app --reload --port 8000
```

```bash
# create
curl -X POST http://127.0.0.1:8000/api/conversations -H "Content-Type: application/json" -d '{"title":"first chat"}'

# list
curl http://127.0.0.1:8000/api/conversations
```

## Output

Create:

```json
{"id": 1, "title": "first chat"}
```

List:

```json
[{"id": 1, "title": "first chat"}]
```

An empty body `{}` creates a conversation with the default title `new chat`.

## Testing

Start the server first (`uvicorn app.main:app --reload --port 8000` from `agent-lab/backend`), then run these curl steps in another terminal.

1. Health still works:

   ```bash
   curl http://127.0.0.1:8000/health
   ```

   Expected: `{"status":"ok","app":"agent lab","debug":true}`

2. Create with an empty body, to check the default title:

   ```bash
   curl -X POST http://127.0.0.1:8000/api/conversations -H "Content-Type: application/json" -d '{}'
   ```

   Expected: `{"id":1,"title":"new chat"}`

3. Create with a custom title:

   ```bash
   curl -X POST http://127.0.0.1:8000/api/conversations -H "Content-Type: application/json" -d '{"title":"verify test"}'
   ```

   Expected: `{"id":2,"title":"verify test"}`

4. List, to check all rows come back newest first:

   ```bash
   curl http://127.0.0.1:8000/api/conversations
   ```

   Expected: `[{"id":2,"title":"verify test"},{"id":1,"title":"new chat"}]`

5. Check the router is mounted in the OpenAPI schema:

   ```bash
   curl http://127.0.0.1:8000/openapi.json
   ```

   Expected paths: `/api/conversations` and `/health`. The interactive docs are at http://127.0.0.1:8000/docs.

### What the tests proved

- The router is mounted: `include_router` exposes `POST` and `GET` on `/api/conversations`.
- `get_db` gives each request a session: rows created by `POST` are visible to the next `GET` request.
- The default title `new chat` is applied when the body has no title.
- The response model returns only `id` and `title` (not `created_at`).
- The list is ordered newest first.
- `/health` and table creation on startup were not broken by the change.

### Notes on the testing

- Steps 2 to 4 were run first with throwaway rows (`new chat`, `verify test`), which were deleted from the `conversation` table afterwards.
- The final run used the title `first chat` (`{"id":1,"title":"first chat"}`); that is the output shown above in "Output".
- Code checks: `ruff check --select I` (import order) passes on `main.py`. Ruff flags `Depends(get_db)` in argument defaults (`B008`) and Pydantic warns that `class Config` is deprecated (use `ConfigDict`). Both are known and left as they are.
- `agent_lab.db` is a local file and is not committed.

# Step 7 - Call an real LLM

## Goal

Replace the echo with a model reply.

## Notes

- Production mainly talks to a LiteLLM proxy.
- Here we call the OpenRouter API directly.
- The key is `OPENROUTER_API_KEY` in `agent-lab/.env` (gitignored), loaded through `config.py` into `settings.openai_api_key`.
- `config.py` also has `openai_base_url` (`https://openrouter.ai/api/v1`) and `openai_model` (`openai/gpt-4o-mini`, GPT-4o mini on OpenRouter).

## What we did

- Added `openai` to `agent-lab/backend/requirements.txt` (Python SDK to call the LLM, used with OpenRouter) and installed the requirements
- Updated `agent-lab/backend/app/config.py` (`Settings`):
  - loads `agent-lab/.env` through an absolute path built from the file location, so it works from any working directory (`extra="ignore"`)
  - `openai_api_key`: default `""`, read from the `OPENROUTER_API_KEY` variable in `.env` (`validation_alias`)
  - `openai_base_url`: `https://openrouter.ai/api/v1`
  - `openai_model`: `openai/gpt-4o-mini` (GPT-4o mini on OpenRouter)
- Created `agent-lab/backend/app/services/` with an empty `__init__.py` and `llm.py`
- `agent-lab/backend/app/services/llm.py`: `get_chat_reply(user_message: str) -> str`
  - raises `RuntimeError("OpenAI API key is not set")` when the key is blank
  - builds `OpenAI(api_key=..., base_url=...)` from settings
  - calls `client.chat.completions.create` with the model from settings, a system message (`"you are helpful assistant"`) and the user message
  - returns `response.choices[0].message.content or ""`
- Added a `Message` model to `agent-lab/backend/app/models.py` (table `message`): `id`, `conversation_id` (foreign key to `conversation.id`, indexed, not null), `role`, `content` (`Text`), `created_at`. The table is created on startup by the existing `create_all`
- Created `agent-lab/backend/app/routers/chat.py`:
  - `router = APIRouter(prefix="/api/chat", tags=["chats"])`
  - `ChatRequest`: `conversation_id: int`, `message: str`
  - `ChatResponse`: `conversation_id: int`, `user_message: str`, `assistant_message: str`
  - `POST /api/chat` (`chat`) uses `get_db` and does the following in order:
    1. looks up the `Conversation` by `body.conversation_id`; returns 404 `Conversation not found` if it is missing
    2. adds the user `Message` (`role="user"`) to the session
    3. calls `get_chat_reply(body.message)`; any exception becomes a 502 with `LLM error: <error>`
    4. adds the assistant `Message` (`role="assistant"`, content = reply), then commits both messages together
    5. returns `ChatResponse`
- Updated `agent-lab/backend/app/main.py` to import `chat` and mount it with `app.include_router(chat.router)` after the conversations router
- Note: the `Message` model and the chat route were built in this step, so the Step 6 pieces (message + simple chat) are covered here, and the echo was never built separately

## Commands

```bash
cd agent-lab/backend
source .venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

```bash
# create a conversation
curl -i -X POST http://127.0.0.1:8000/api/conversations -H "Content-Type: application/json" -d '{"title":"llm test"}'

# chat in a conversation (a real call to OpenRouter, costs a small amount of credit)
curl -i -X POST http://127.0.0.1:8000/api/chat -H "Content-Type: application/json" -d '{"conversation_id":1,"message":"Say hello in one short sentence."}'
```

## Output

Create a conversation:

```json
{"id": 2, "title": "llm test"}
```

Chat (HTTP 200):

```json
{"conversation_id": 1, "user_message": "Say hello in one short sentence.", "assistant_message": "Hello!"}
```

Unknown conversation (HTTP 404):

```json
{"detail": "Conversation not found"}
```

## Testing

1. `GET /health` returned 200 with `{"status":"ok","app":"agent lab","debug":true}`, so the app still starts with the new router.
2. `POST /api/conversations` returned 200 with `{"id":2,"title":"llm test"}`.
3. `POST /api/chat` with `conversation_id` 1 returned 200 and the model reply `Hello!`. This was a real call to OpenRouter with `openai/gpt-4o-mini`.
4. The database was checked directly in `agent_lab.db`. The `message` table had two rows for conversation 1:
   - `user`: `Say hello in one short sentence.`
   - `assistant`: `Hello!`
5. `POST /api/chat` with `conversation_id` 999 returned 404 `Conversation not found`, and no message row was saved for it.

### What the tests proved

- The key loads from `agent-lab/.env` and the OpenRouter call works with the configured base URL and model.
- The user message and the assistant reply are both saved, in order, in the `message` table.
- A missing conversation stops the request before the LLM is called or anything is saved.

### Notes on the testing

- Not tested: the 502 path (`LLM error: ...`) and the `RuntimeError` for a blank key. Both come from the code but were not triggered.
- The first start failed with `ImportError: cannot import name 'Message'` and then `No module named 'openai'`, because the model was missing and the package was not installed. Adding `Message` and running `pip install -r requirements.txt` fixed both.
- The 502 response includes the raw error text from the call, so it can show provider error details to the client.
- Code checks: ruff import order and unused-import checks pass on all changed files. Ruff formatting passes on `config.py`, `models.py` and `services/llm.py`. `main.py` (the hand-formatted `/health` return) and `routers/chat.py` (the hand-written 404 block with an odd line break and trailing spaces) would still be reformatted by ruff; they were left as written.
- `agent_lab.db` (with the test rows) and `agent-lab/.env` (the key) are local and are not committed.
