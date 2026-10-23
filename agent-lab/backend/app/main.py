from fastapi import FastAPI

app = FastAPI(title="agent lab")


@app.get("/health")
def health():
    return {"status": "ok"}
