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

# Step 8 - Conversation history

## Goal

Send all prior messages of the conversation to the LLM, not only the latest one.

## Why this step

- Right now the model is forgetful each turn.
- `get_chat_reply` sends only the system prompt and the latest user message, even though every earlier message is saved in the `message` table.
- Any real chat app builds a message list from the DB and sends it to the model each turn.

## What we did

- Changed `agent-lab/backend/app/services/llm.py`: `get_chat_reply(user_message: str)` became `get_chat_reply(history: list[dict[str, str]]) -> str`
  - `history` is a list of `{"role": ..., "content": ...}` dictionaries, for example `[{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}, {"role": "user", "content": "how are you"}]` (kept as a docstring example)
  - the message list sent to the model is now the system prompt followed by the whole history: `messages = [system]`, then `messages.extend(history)`
- Changed only the LLM call part of `chat()` in `agent-lab/backend/app/routers/chat.py`:
  1. before calling the LLM, load the conversation's saved messages from the DB (`Message` rows filtered by `conversation_id`, ordered by `Message.id`)
  2. turn them into `history = [{"role": m.role, "content": m.content}, ...]`
  3. append the new user message to `history` in memory: `history.append({"role": "user", "content": body.message})`
  4. call `get_chat_reply(history)` instead of `get_chat_reply(body.message)`
- Why the new message is appended by hand: `database.py` uses `autoflush=False`, so the new user `Message` that was only `db.add`-ed is not visible to the query yet. The query returns only the earlier messages, and the new one is added once, in memory. If autoflush were turned on, the new message would appear twice
- Everything else in `chat()` is unchanged: 404 for an unknown conversation, 502 on an LLM error, saving both messages and one commit at the end

## Commands

```bash
cd agent-lab/backend
source .venv/Scripts/activate
uvicorn app.main:app --reload --port 8000
```

## How to test memory with curl

Start the server first, then run this in another terminal. It creates a conversation, sends three turns, and the last turn only works if the model sees the earlier ones.

```bash
B=http://127.0.0.1:8000
J='Content-Type: application/json'

# 1. create a conversation and keep its id
CID=$(curl -sS -X POST $B/api/conversations -H "$J" -d '{"title":"history test"}' | python -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "conversation id: $CID"

# 2. turn 1: tell the model a fact
curl -sS -X POST $B/api/chat -H "$J" -d "{\"conversation_id\":$CID,\"message\":\"My name is Pushpender and my favourite colour is green. Just say OK.\"}"

# 3. turn 2: ask about it, in the SAME conversation (this needs history)
curl -sS -X POST $B/api/chat -H "$J" -d "{\"conversation_id\":$CID,\"message\":\"What is my name and my favourite colour?\"}"

# 4. control: ask the same question in a NEW conversation (it should not know)
CID2=$(curl -sS -X POST $B/api/conversations -H "$J" -d '{"title":"no memory control"}' | python -c "import sys,json; print(json.load(sys.stdin)['id'])")
curl -sS -X POST $B/api/chat -H "$J" -d "{\"conversation_id\":$CID2,\"message\":\"What is my name and my favourite colour?\"}"

# 5. unknown conversation (expect 404)
curl -i -X POST $B/api/chat -H "$J" -d '{"conversation_id":9999,"message":"hi"}'
```

What to look for:

- Turn 2 answers with the name and colour from turn 1. Before this step the model could not do that, because it only saw the latest message.
- The control conversation says it does not know, so history stays inside one conversation.
- Step 5 returns `404` with `{"detail":"Conversation not found"}`.

To see what was saved, run this from `agent-lab/backend` (replace `3` with your conversation id):

```bash
.venv/Scripts/python.exe -c "import sqlite3; [print(r) for r in sqlite3.connect('agent_lab.db').execute('select id, role, content from message where conversation_id=3 order by id')]"
```

## Output

Turn 1 (`{"conversation_id":3,...}`):

```json
{"conversation_id":3,"user_message":"My name is Pushpender and my favourite colour is green. Just say OK.","assistant_message":"OK."}
```

Turn 2, same conversation:

```json
{"conversation_id":3,"user_message":"What is my name and my favourite colour?","assistant_message":"Your name is Pushpender, and your favourite colour is green."}
```

Control, new conversation, same question:

```json
{"conversation_id":4,"user_message":"What is my name and my favourite colour?","assistant_message":"I'm sorry, but I don't know your name or your favorite color. If you tell me, I’d be happy to remember them for this conversation!"}
```

Rows saved for conversation 3:

```
(3, 'user', 'My name is Pushpender and my favourite colour is green. Just say OK.')
(4, 'assistant', 'OK.')
(5, 'user', 'What is my name and my favourite colour?')
(6, 'assistant', 'Your name is Pushpender, and your favourite colour is green.')
```

## Testing

Two real runs against OpenRouter (`openai/gpt-4o-mini`), both with curl:

1. Two-turn memory test (above): turn 2 recalled the name and the colour, and the control conversation did not know them.
2. Three-turn test with facts spread over two turns:
   - turn 1: `I am planning a trip to Jaipur in December.`
   - turn 2: `My budget is 20000 rupees.` The reply already assumed Jaipur
   - turn 3: `Remind me: where am I going, when, and what is my budget? Answer in one sentence.` Reply: `You are going to Jaipur in December, with a budget of 20,000 rupees.`
3. `POST /api/chat` with `conversation_id` 9999 returned `404 {"detail":"Conversation not found"}`.

### What the tests proved

- The model now sees every earlier message of the conversation, not only the latest one.
- Memory is per conversation: a new conversation starts empty.
- Each turn saves exactly two rows (user, then assistant) in order, with no duplicates, so appending the new message in memory works as intended.
- The 404 path still works and calls neither the LLM nor saves anything.

### Notes on the testing

- History is sent in full on every turn with no limit. Long conversations cost more each turn and will eventually reach the model's context limit. Trimming or summarizing is not done yet.
- The replies were long because the system prompt does not ask for short answers. That affects cost and speed, not correctness.
- Not tested: the 502 path (`LLM error: ...`) and the blank-key `RuntimeError`.
- Code checks: ruff import order and unused-name checks pass on `chat.py` and `llm.py`. Ruff formatting would still change a few hand-written spots (the 404 block in `chat.py` and spacing in the `messages` list in `llm.py`); they were left as written.
- The tests left conversations 3, 4 and 5 in the local `agent_lab.db`, which is not committed.

# Step 9 - One tool (function calling)

## Goal

The model can call a tool, we run it, and send the result back.

## Notes

- The tool we use is `get_current_time`. It returns the current UTC time as text.
- Function calling in short: we tell the model which tools exist, the model answers with a tool call (a tool name and arguments) instead of text, we run the tool ourselves, send the result back as a `tool` message, and call the model again to get the final text.
- The model never runs anything. It only asks, and our code runs the tool.

## What we did

- Created `agent-lab/backend/app/services/tools.py`:
  - `get_current_time() -> str` returns `datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")`, for example `2026-10-23 15:06:41 UTC`
  - `TOOL_DEFINITION`: the tool description sent to the model (`type: function`, name `get_current_time`, description `get the current date and time in UTC`, parameters: an empty object, `properties` `{}`, `additionalProperties` `False`)
  - `run_tool(name: str, arguments: dict[str, str]) -> str` runs the tool by name: `get_current_time` returns the time, any other name returns `unknown tool <name>`
- Updated `agent-lab/backend/app/services/llm.py` (`get_chat_reply`):
  - imports `json` and `from app.services.tools import TOOL_DEFINITION, run_tool`
  - the first model call now passes `tools=[TOOL_DEFINITION]`
  - if the reply has `tool_calls`:
    1. append the model's message (the one that holds the tool calls) to `messages`
    2. for each tool call, parse its arguments with `json.loads(... or "{}")`, run `run_tool(name, arguments)`, and append `{"role": "tool", "tool_call_id": <id>, "content": <result>}`
    3. call the model again with `messages` (and `tools` again) and use that reply
  - returns `message.content or ""`
  - the system prompt is now `you are helpful assistant. Use tools to get the information you need.` and `messages` is annotated `list[dict[str, str]]`
- Fixed a bug in `agent-lab/backend/app/routers/chat.py` found while testing: the history query was wrapped in `{ }` (a Python set), so every `POST /api/chat` returned 500 with `TypeError: cannot use 'list' as a set element`. It is now wrapped in `( )`. That bug was already in the Step 8 commit
- `chat.py` did not need any other change, because the tool round happens inside `get_chat_reply`

## Commands

```bash
cd agent-lab/backend
source .venv/Scripts/activate
uvicorn app.main:app --port 8000
```

```bash
B=http://127.0.0.1:8000
J='Content-Type: application/json'

# create a conversation and keep its id
CID=$(curl -sS -X POST $B/api/conversations -H "$J" -d '{"title":"tool test"}' | python -c "import sys,json; print(json.load(sys.stdin)['id'])")

# 1. time question (the model should call the tool)
curl -sS -X POST $B/api/chat -H "$J" -d "{\"conversation_id\":$CID,\"message\":\"What is the current date and time in UTC?\"}"

# 2. plain question (no tool needed)
curl -sS -X POST $B/api/chat -H "$J" -d "{\"conversation_id\":$CID,\"message\":\"Say hello in one short sentence.\"}"

# 3. memory still works after a tool turn
curl -sS -X POST $B/api/chat -H "$J" -d "{\"conversation_id\":$CID,\"message\":\"What did I ask you first?\"}"

# 4. unknown conversation (expect 404)
curl -i -X POST $B/api/chat -H "$J" -d '{"conversation_id":9999,"message":"hi"}'

# compare with the real clock
date -u
```

How to tell the tool really ran: the model cannot know the current time by itself, so if the reply matches `date -u` to the minute, the tool was called.

## Output

Time question (HTTP 200, real clock was `15:06:45`):

```json
{"conversation_id":7,"user_message":"What is the current date and time in UTC?","assistant_message":"The current date and time in UTC is 2026-10-23 15:06:41."}
```

Plain question (HTTP 200):

```json
{"conversation_id":7,"user_message":"Say hello in one short sentence.","assistant_message":"Hello! How can I assist you today?"}
```

Memory after a tool turn (HTTP 200):

```json
{"conversation_id":7,"user_message":"What did I ask you first?","assistant_message":"You asked for the current date and time in UTC."}
```

Unknown conversation (HTTP 404):

```json
{"detail":"Conversation not found"}
```

Rows saved for conversation 7:

```
(15, 'user', 'What is the current date and time in UTC?')
(16, 'assistant', 'The current date and time in UTC is 2026-10-23 15:06:41.')
(17, 'user', 'Say hello in one short sentence.')
(18, 'assistant', 'Hello! How can I assist you today?')
(19, 'user', 'What did I ask you first?')
(20, 'assistant', 'You asked for the current date and time in UTC.')
```

## Testing

Real runs against OpenRouter (`openai/gpt-4o-mini`), with curl against the running server:

1. First curl run: every `POST /api/chat` returned 500. The server log showed `TypeError: cannot use 'list' as a set element (unhashable type: 'list')` in `chat.py`. The history query was wrapped in `{ }`. Changing it to `( )` fixed it, and the server was restarted (it runs without `--reload`).
2. Time question returned 200 with `2026-10-23 15:06:41`, matching the real clock (`15:06:45`), so the tool ran.
3. Plain question returned 200 with a normal reply and no tool call.
4. Third question in the same conversation recalled the first question, so history still works with tool turns.
5. `conversation_id` 9999 returned 404 `Conversation not found`.
6. The database held exactly six rows for the conversation, alternating user and assistant, with no duplicates.
7. After the system prompt was edited, `get_chat_reply` was run directly once more: the time question returned `15:07:25` (real clock `15:07:28`) and the plain question returned `Hello!`. This second check did not go through curl.

### What the tests proved

- The model asked for `get_current_time`, our code ran it, and the second model call used the result in its answer.
- Questions that need no tool still work and make a single model call.
- History and saving are unaffected by the tool round.

### Notes on the testing

- Only the final assistant reply is saved. The tool call and the tool result are not stored in the `message` table. On later turns the model sees only the final text, which was enough for the memory test.
- There is a single tool round. If the model asked for another tool on the second call, the reply would be empty (`message.content or ""`). A loop is not built.
- Not tested: an unknown tool name from the model, and the 502 and blank-key paths.
- `tools` is sent again on the second call, which was our choice and was not part of the dictation.
- Code checks: ruff import order and unused-name checks pass on `tools.py`, `llm.py` and `chat.py`. Ruff formatting passes on `tools.py`. It would still change the hand-written spots in `llm.py` (the long system prompt line and `messages= messages`) and `chat.py` (the `conversation` query and the 404 block); they were left as written.
- The tests left conversations 6 and 7 in the local `agent_lab.db`, which is not committed.
