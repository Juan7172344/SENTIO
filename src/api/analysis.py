"""Endpoint de análisis de riesgo a partir del perfil persistido."""

from __future__ import annotations

import sqlite3
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from src import db as db_module
from src.db import get_db

router = APIRouter(tags=["Analysis"])


class AnalyzeRequest(BaseModel):
    user_id: str = Field(..., description="UUID del perfil en `student_profiles.id`")


@router.post("/analyze")
def analyze_profile(
    request: Request,
    body: AnalyzeRequest,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> dict[str, Any]:
    engine = getattr(request.app.state, "inference_engine", None)
    if engine is None:
        raise HTTPException(status_code=503, detail="Inference engine not initialized")

    profile = db_module.get_profile_by_id(conn, body.user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")

    payload = db_module.profile_as_model_inputs(profile)
    result = engine.predict_risk(payload)
    return {
        "user_id": profile.id,
        "career": profile.career,
        **result,
        "confidence_score": result["confidence"],
        "disclaimer": "Esta evaluación es orientativa y no constituye un diagnóstico clínico.",
    }
