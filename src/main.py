"""Aplicación FastAPI con plantillas Jinja2 y motor de inferencia."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import Response

load_dotenv()

from model.inference import SentioInferenceEngine
from src import db as db_module
from src.api import analysis as analysis_routes
from src.config import model_artifact_path, secret_key
from src.routes import web as web_routes


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        conn = db_module.connect()
        db_module.init_schema(conn)
        conn.close()
        engine = SentioInferenceEngine(model_artifact_path())
        engine.warmup()
        app.state.inference_engine = engine
        yield

    application = FastAPI(
        title="SENTIO",
        description="Monitoreo del bienestar emocional estudiantil (bootstrap).",
        version="0.1.0",
        lifespan=lifespan,
    )

    application.add_middleware(SessionMiddleware, secret_key=secret_key())
    application.include_router(web_routes.router)
    application.include_router(analysis_routes.router)

    static_dir = Path(__file__).resolve().parent / "static"
    if static_dir.is_dir():
        application.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @application.get("/.well-known/appspecific/com.chrome.devtools.json", include_in_schema=False)
    def chrome_devtools_well_known() -> Response:
        return Response(content="{}", media_type="application/json")

    @application.get("/favicon.ico", include_in_schema=False)
    def favicon() -> Response:
        return Response(status_code=204)

    return application


app = create_app()
