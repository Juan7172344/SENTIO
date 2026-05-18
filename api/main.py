"""Punto de entrada FastAPI del monorepo (evolución).

Para el prototipo con Jinja2, ejecuta `python -m uvicorn src.main:app`.
"""

from fastapi import FastAPI

app = FastAPI(title="SENTIO API (stub)", version="0.0.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
