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
