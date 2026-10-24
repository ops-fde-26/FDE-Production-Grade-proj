# Agent Lab - Project Summary (in simple words)

## What is this project?

Agent Lab is a small chat backend. You send it a message, it asks an AI model for a reply, saves the whole chat in a database, and sends the reply back.

It was built step by step to learn how a real production backend is put together. The detailed notes for each step are in `STEPS.md`, and the progress table is in `LEARNING.md`.

## What can it do now?

1. Say it is alive (`/health`).
2. Create and list conversations (chat threads).
3. Chat inside a conversation. The AI reply is real (OpenRouter, model `openai/gpt-4o-mini`).
4. Remember the chat. Every earlier message of the conversation is sent to the AI each time, so it remembers what you said.
5. Use a tool. If you ask for the time, the AI asks our code to run `get_current_time`, and then uses the answer.
6. Use an agent. An agent is just a name plus an instruction (for example "You are a pirate"). A conversation can be linked to an agent, and then the AI follows that instruction.

## How one chat message travels

```
you (curl)
   |  POST /api/chat  {"conversation_id": 1, "message": "hi"}
   v
chat.py            finds the conversation, finds its agent (if any),
   |               loads the old messages, adds your new message
   v
llm.py             sends system prompt + history to the AI model
   |               if the AI asks for a tool -> tools.py runs it -> AI is called again
   v
chat.py            saves your message and the AI reply in the database
   |
   v
you get the reply
```

## The 10 steps we did

| Step | What we built | In one line |
|---|---|---|
| 0 | Repo + git + `LEARNING.md` | A place to work and a log of what we learn |
| 1 | FastAPI hello (`main.py`) | A web app with `/health` |
| 2 | Settings (`config.py`) | One place for configuration, loaded from `.env` |
| 3 | Database (`database.py`) | Connection to SQLite and a `get_db` helper for routes |
| 4 | First model (`Conversation`) | A database table written as a Python class |
| 5 | Conversations API | Create and list conversations over HTTP |
| 6 | Message + simple chat | Covered inside step 7 (we never built a separate echo) |
| 7 | Call a real LLM | `Message` table, `/api/chat`, and the OpenRouter call in `llm.py` |
| 8 | Conversation history | Send all earlier messages to the AI, so it remembers |
| 9 | One tool | `get_current_time`, and the "AI asks, we run, AI answers" loop |
| 10 | Simple agent | Agent = name + instruction, linked to a conversation, used as the system prompt |

## Folder map

```
LEARNING.md                 progress table (step / topic / status)
STEPS.md                    detailed notes for every step
PROJECT.md                  this file
agent-lab/
  .env                      your API key (never committed)
  backend/
    requirements.txt        the Python packages
    agent_lab.db            the SQLite database (local, never committed)
    app/
      main.py               starts the app and plugs in the routers
      config.py             settings (API key, model, app name)
      database.py           database engine, sessions, get_db
      models.py             tables: Agent, Conversation, Message
      routers/
        conversations.py    create / list conversations
        chat.py             the chat endpoint
        agent.py            create / list agents
      services/
        llm.py              talks to the AI model, runs the tool loop
        tools.py            the tool definition and the tool itself
```

## The database (3 tables)

- `agent`: `id`, `name`, `instruction`
- `conversation`: `id`, `title`, `agent_id` (optional), `created_at`
- `message`: `id`, `conversation_id`, `role` (`user` or `assistant`), `content`, `created_at`

## The API

| Method | Path | What it does |
|---|---|---|
| GET | `/health` | Shows the app is running |
| POST | `/api/conversations` | Creates a conversation. Body: `title` (optional), `agent_id` (optional) |
| GET | `/api/conversations` | Lists conversations, newest first |
| POST | `/api/chat` | Sends a message. Body: `conversation_id`, `message`. Returns the AI reply |
| POST | `/api/agent` | Creates an agent. Body: `name`, `instruction` (optional) |
| GET | `/api/agent` | Lists agents, newest first |

Errors: `404` when the conversation does not exist, `502` when the AI call fails.

## How to run it

```bash
cd agent-lab/backend
python -m venv .venv
source .venv/Scripts/activate        # Git Bash on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

You need a file `agent-lab/.env` with one line: `OPENROUTER_API_KEY=your key`. Open `http://127.0.0.1:8000/docs` to try the API in the browser.

## Quick test with curl

```bash
B=http://127.0.0.1:8000
J='Content-Type: application/json'

# make an agent
curl -X POST $B/api/agent -H "$J" -d '{"name":"pirate","instruction":"You are a pirate. Answer in one short sentence."}'

# make a conversation that uses agent 1
curl -X POST $B/api/conversations -H "$J" -d '{"title":"pirate chat","agent_id":1}'

# chat (the reply should sound like a pirate)
curl -X POST $B/api/chat -H "$J" -d '{"conversation_id":1,"message":"How are you today?"}'

# ask for the time (the AI uses the tool)
curl -X POST $B/api/chat -H "$J" -d '{"conversation_id":1,"message":"What is the current date and time in UTC?"}'
```

## Good to know

- **Real AI calls cost a little credit.** Every chat message calls OpenRouter.
- **Old database + new column:** `create_all` makes new tables but never adds a column to an old table. If your `agent_lab.db` was made before step 10, run `ALTER TABLE conversation ADD COLUMN agent_id INTEGER` once, or delete the file and let it be recreated.
- **Agent instruction replaces the whole system prompt.** The default prompt says "Use tools to get the information you need". An agent's instruction does not include that sentence unless you write it.
- **A missing agent is ignored.** If a conversation points to an agent id that does not exist, the default prompt is used and nothing fails.
- **Tool calls are not saved.** Only your message and the final AI reply go into the `message` table.
- **One tool round only.** The AI can call tools once per message. A longer loop is not built.
- **History is not trimmed.** Very long conversations will cost more and will eventually hit the model's limit.
- **Never committed:** `agent-lab/.env` (the key) and `agent_lab.db` (test data).

## Ideas for what to build next

- Save tool calls and results in the database.
- Let the AI call more than one tool in a row (a loop).
- Add more tools.
- Trim or summarise long histories.
- Add update and delete for agents, and check that `agent_id` exists when creating a conversation.
- Use a proper migration tool (like Alembic) instead of `create_all`.
- Use Postgres instead of SQLite, and a LiteLLM proxy instead of calling OpenRouter directly (the production style).
