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
