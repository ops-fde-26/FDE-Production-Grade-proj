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
