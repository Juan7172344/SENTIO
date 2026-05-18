"""Rutas HTML (Jinja2): onboarding en 3 pasos (prototipo) e inicio tipo dashboard."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Annotated, Any, List, Optional
from uuid import uuid4
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src import db as db_module
from src.config import dev_reset_enabled
from src.db import get_db

router = APIRouter()
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

DRAFT_KEY = "sentio_onboarding_draft"


def _ensure_session_key(request: Request) -> str:
    existing = request.session.get("sentio_session_key")
    if existing:
        return str(existing)
    session_key = str(uuid4())
    request.session["sentio_session_key"] = session_key
    return session_key


def _draft_get(request: Request) -> dict[str, Any]:
    raw = request.session.get(DRAFT_KEY)
    return dict(raw) if isinstance(raw, dict) else {}


def _draft_save(request: Request, **kwargs: Any) -> None:
    data = _draft_get(request)
    data.update(kwargs)
    request.session[DRAFT_KEY] = data


def _draft_clear(request: Request) -> None:
    request.session.pop(DRAFT_KEY, None)


def _fmt_sleep_hours(value: float) -> str:
    text = f"{float(value):.2f}".rstrip("0").rstrip(".")
    return text or "0"


def _profile_redirect(
    conn: sqlite3.Connection,
    session_key: str,
) -> RedirectResponse | None:
    if db_module.get_profile_by_session(conn, session_key) is not None:
        return RedirectResponse(url="/inicio", status_code=303)
    return None


@router.get("/", response_class=HTMLResponse)
@router.get("/onboarding", response_class=HTMLResponse)
def onboarding_entry(
    request: Request,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> Any:
    session_key = _ensure_session_key(request)
    redir = _profile_redirect(conn, session_key)
    if redir:
        return redir
    return RedirectResponse(url="/onboarding/paso-1", status_code=303)


@router.get("/onboarding/paso-1", response_class=HTMLResponse)
def onboarding_paso1_get(
    request: Request,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> Any:
    session_key = _ensure_session_key(request)
    redir = _profile_redirect(conn, session_key)
    if redir:
        return redir
    draft = _draft_get(request)
    values = {
        "age": draft.get("age", ""),
        "career": draft.get("career", ""),
        "semester": draft.get("semester", ""),
    }
    return templates.TemplateResponse(
        request=request,
        name="onboarding_paso1.html",
        context={"errors": {}, "values": values},
    )


@router.post("/onboarding/paso-1", response_class=HTMLResponse)
def onboarding_paso1_post(
    request: Request,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
    age: Annotated[int, Form()],
    career: Annotated[str, Form()],
    semester: Annotated[int, Form()],
) -> Any:
    session_key = _ensure_session_key(request)
    redir = _profile_redirect(conn, session_key)
    if redir:
        return redir

    errors: dict[str, str] = {}
    career_clean = career.strip()
    if not career_clean:
        errors["career"] = "La carrera es obligatoria."
    if age < 16 or age > 90:
        errors["age"] = "Indica una edad plausible (16–90)."
    if semester < 1 or semester > 20:
        errors["semester"] = "Indica un semestre entre 1 y 20."

    values = {"age": age, "career": career, "semester": semester}
    if errors:
        return templates.TemplateResponse(
            request=request,
            name="onboarding_paso1.html",
            context={"errors": errors, "values": values},
            status_code=422,
        )

    _draft_save(
        request,
        age=age,
        career=career_clean,
        semester=semester,
    )
    return RedirectResponse(url="/onboarding/paso-2", status_code=303)


@router.get("/onboarding/paso-2", response_class=HTMLResponse)
def onboarding_paso2_get(
    request: Request,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> Any:
    session_key = _ensure_session_key(request)
    redir = _profile_redirect(conn, session_key)
    if redir:
        return redir
    draft = _draft_get(request)
    if not draft.get("career"):
        return RedirectResponse(url="/onboarding/paso-1", status_code=303)

    sleep = float(draft.get("habitual_sleep_hours", 7.0))
    stress = int(draft.get("base_academic_stress", 5))
    return templates.TemplateResponse(
        request=request,
        name="onboarding_paso2.html",
        context={
            "errors": {},
            "habitual_sleep_hours": sleep,
            "base_academic_stress": stress,
            "sleep_display": _fmt_sleep_hours(sleep),
        },
    )


@router.post("/onboarding/paso-2", response_class=HTMLResponse)
def onboarding_paso2_post(
    request: Request,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
    habitual_sleep_hours: Annotated[float, Form()],
    base_academic_stress: Annotated[int, Form()],
) -> Any:
    session_key = _ensure_session_key(request)
    redir = _profile_redirect(conn, session_key)
    if redir:
        return redir
    draft = _draft_get(request)
    if not draft.get("career"):
        return RedirectResponse(url="/onboarding/paso-1", status_code=303)

    errors: dict[str, str] = {}
    if not (4.0 <= habitual_sleep_hours <= 12.0):
        errors["habitual_sleep_hours"] = "Las horas de sueño deben estar entre 4 y 12."
    if not (1 <= base_academic_stress <= 10):
        errors["base_academic_stress"] = "El estrés debe estar entre 1 y 10."

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="onboarding_paso2.html",
            context={
                "errors": errors,
                "habitual_sleep_hours": habitual_sleep_hours,
                "base_academic_stress": base_academic_stress,
                "sleep_display": _fmt_sleep_hours(habitual_sleep_hours),
            },
            status_code=422,
        )

    _draft_save(
        request,
        habitual_sleep_hours=float(habitual_sleep_hours),
        base_academic_stress=int(base_academic_stress),
    )
    return RedirectResponse(url="/onboarding/paso-3", status_code=303)


@router.get("/onboarding/paso-3", response_class=HTMLResponse)
def onboarding_paso3_get(
    request: Request,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> Any:
    session_key = _ensure_session_key(request)
    redir = _profile_redirect(conn, session_key)
    if redir:
        return redir
    draft = _draft_get(request)
    if not draft.get("career"):
        return RedirectResponse(url="/onboarding/paso-1", status_code=303)
    if "habitual_sleep_hours" not in draft or "base_academic_stress" not in draft:
        return RedirectResponse(url="/onboarding/paso-2", status_code=303)

    act = int(draft.get("physical_activity_days_per_week", 3))
    act = max(0, min(7, act))
    return templates.TemplateResponse(
        request=request,
        name="onboarding_paso3.html",
        context={"errors": {}, "physical_activity_days_per_week": act},
    )


@router.post("/onboarding/paso-3", response_class=HTMLResponse)
def onboarding_paso3_post(
    request: Request,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
    physical_activity_days_per_week: Annotated[int, Form()],
) -> Any:
    session_key = _ensure_session_key(request)
    redir = _profile_redirect(conn, session_key)
    if redir:
        return redir
    draft = _draft_get(request)
    if not draft.get("career") or "base_academic_stress" not in draft:
        return RedirectResponse(url="/onboarding/paso-1", status_code=303)

    errors: dict[str, str] = {}
    if not (0 <= physical_activity_days_per_week <= 7):
        errors["physical_activity_days_per_week"] = "Selecciona entre 0 y 7 días."

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="onboarding_paso3.html",
            context={
                "errors": errors,
                "physical_activity_days_per_week": physical_activity_days_per_week,
            },
            status_code=422,
        )

    db_module.insert_profile(
        conn,
        session_key=session_key,
        age=int(draft["age"]),
        career=str(draft["career"]),
        semester=int(draft["semester"]),
        habitual_sleep_hours=float(draft["habitual_sleep_hours"]),
        physical_activity_days_per_week=int(physical_activity_days_per_week),
        base_academic_stress=int(draft["base_academic_stress"]),
    )
    request.session["welcome_career"] = str(draft["career"])
    _draft_clear(request)
    return RedirectResponse(url="/inicio", status_code=303)


@router.get("/inicio", response_class=HTMLResponse)
def home_page(
    request: Request,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> Any:
    import datetime
    session_key = _ensure_session_key(request)
    profile = db_module.get_profile_by_session(conn, session_key)
    if profile is None:
        return RedirectResponse(url="/onboarding/paso-1", status_code=303)

    welcome_career = request.session.pop("welcome_career", None)
    engine = getattr(request.app.state, "inference_engine", None)
    
    records = db_module.get_daily_records_by_user(conn, profile.id, limit=7)
    today_str = date.today().isoformat()
    registered_today = any(r.record_date == today_str for r in records)
    
    racha = 0
    current_date = date.today()
    for i, r in enumerate(records):
        if r.record_date == current_date.isoformat():
            racha += 1
            current_date -= datetime.timedelta(days=1)
        elif r.record_date == (current_date - datetime.timedelta(days=1)).isoformat() and i == 0:
            racha += 1
            current_date -= datetime.timedelta(days=2)
        else:
            break
            
    esta_semana = len([r for r in records if (date.today() - datetime.date.fromisoformat(r.record_date)).days < 7])

    if engine is not None:
        user_vec = db_module.profile_as_model_inputs(profile)
        if records:
            user_vec["base_academic_stress"] = float(records[0].stress_level)
            user_vec["habitual_sleep_hours"] = float(records[0].sleep_hours)
        analysis = engine.predict_risk(user_vec)
    else:
        analysis = {
            "risk": False,
            "risk_level": "Bajo",
            "confidence": 0.0,
            "source": "Clinical",
            "message": "Motor de inferencia no disponible.",
        }

    return templates.TemplateResponse(
        request=request,
        name="inicio.html",
        context={
            "profile": profile,
            "welcome_career": welcome_career,
            "show_dev_reset": dev_reset_enabled(),
            "analysis": analysis,
            "racha": racha,
            "esta_semana": esta_semana,
            "registered_today": registered_today,
        },
    )


@router.get("/registro", response_class=HTMLResponse)
def registro_diario_get(
    request: Request,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> Any:
    session_key = _ensure_session_key(request)
    profile = db_module.get_profile_by_session(conn, session_key)
    if profile is None:
        return RedirectResponse(url="/onboarding/paso-1", status_code=303)
    
    return templates.TemplateResponse(
        request=request,
        name="registro_diario.html",
        context={"error": None},
    )


@router.post("/registro", response_class=HTMLResponse)
async def registro_diario_post(
    request: Request,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> Any:
    session_key = _ensure_session_key(request)
    profile = db_module.get_profile_by_session(conn, session_key)
    if profile is None:
        return RedirectResponse(url="/onboarding/paso-1", status_code=303)
    
    form = await request.form()
    mood = int(form.get("mood", 3))
    energy = int(form.get("energy", 3))
    sleep_hours = float(form.get("sleep_hours", 7.0))
    stress_level = int(form.get("stress_level", 5))
    activities = form.getlist("activities")
    
    today_str = date.today().isoformat()
    
    try:
        record = db_module.insert_daily_record(
            conn,
            user_id=profile.id,
            record_date=today_str,
            mood=mood,
            energy=energy,
            sleep_hours=sleep_hours,
            stress_level=stress_level,
            activities=activities,
        )
        # Pass the record ID to the session to show in the summary
        request.session["last_record_id"] = record.id
        return RedirectResponse(url="/resumen", status_code=303)
    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="registro_diario.html",
            context={"error": "Ya tienes un registro para el día de hoy o ha ocurrido un error."},
            status_code=400,
        )


@router.get("/resumen", response_class=HTMLResponse)
def resumen_dia(
    request: Request,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> Any:
    session_key = _ensure_session_key(request)
    profile = db_module.get_profile_by_session(conn, session_key)
    if profile is None:
        return RedirectResponse(url="/onboarding/paso-1", status_code=303)
    
    records = db_module.get_daily_records_by_user(conn, profile.id, limit=1)
    if not records:
        return RedirectResponse(url="/registro", status_code=303)
    
    return templates.TemplateResponse(
        request=request,
        name="resumen_dia.html",
        context={"record": records[0]},
    )


@router.get("/evaluacion", response_class=HTMLResponse)
def evaluacion_ia(
    request: Request,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> Any:
    session_key = _ensure_session_key(request)
    profile = db_module.get_profile_by_session(conn, session_key)
    if profile is None:
        return RedirectResponse(url="/onboarding/paso-1", status_code=303)
    
    engine = getattr(request.app.state, "inference_engine", None)
    if engine is not None:
        user_vec = db_module.profile_as_model_inputs(profile)
        records = db_module.get_daily_records_by_user(conn, profile.id, limit=1)
        if records:
            user_vec["base_academic_stress"] = float(records[0].stress_level)
            user_vec["habitual_sleep_hours"] = float(records[0].sleep_hours)
        analysis = engine.predict_risk(user_vec)
        
        # Save to DB
        db_module.insert_risk_assessment(
            conn,
            user_id=profile.id,
            risk_level=analysis.get("risk_level", "Medio"),
            confidence_score=analysis.get("confidence", 0.0),
            decision_source=analysis.get("source", "ml"),
            rule_code=None,
            data_quality_flag="ok",
            days_analyzed=1,
            raw_features=user_vec,
            probabilities={"confidence": analysis.get("confidence", 0.0)}
        )
    else:
        analysis = {
            "risk_level": "Medio",
            "message": "Motor de inferencia no disponible. Mostrando datos por defecto.",
        }
    
    return templates.TemplateResponse(
        request=request,
        name="evaluacion_ia.html",
        context={
            "risk_level": analysis.get("risk_level", "Medio"),
            "explanation": analysis.get("message", ""),
        },
    )


@router.get("/recomendaciones", response_class=HTMLResponse)
def recomendaciones_get(
    request: Request,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> Any:
    session_key = _ensure_session_key(request)
    if db_module.get_profile_by_session(conn, session_key) is None:
        return RedirectResponse(url="/onboarding/paso-1", status_code=303)
    
    return templates.TemplateResponse(
        request=request,
        name="recomendaciones.html",
        context={},
    )


@router.get("/analisis", response_class=HTMLResponse)
def analisis_semanal(
    request: Request,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> Any:
    session_key = _ensure_session_key(request)
    profile = db_module.get_profile_by_session(conn, session_key)
    if profile is None:
        return RedirectResponse(url="/onboarding/paso-1", status_code=303)
    
    records = db_module.get_daily_records_by_user(conn, profile.id, limit=7)
    
    avg_mood = sum(r.mood for r in records) / len(records) if records else profile.base_academic_stress / 2.0
    avg_energy = sum(r.energy for r in records) / len(records) if records else 3.0
    avg_sleep = sum(r.sleep_hours for r in records) / len(records) if records else profile.habitual_sleep_hours
    avg_stress = sum(r.stress_level for r in records) / len(records) if records else profile.base_academic_stress
    
    metrics = {
        "avg_mood": avg_mood,
        "avg_energy": avg_energy,
        "avg_sleep": avg_sleep,
        "avg_stress": avg_stress,
    }
    
    return templates.TemplateResponse(
        request=request,
        name="analisis_semanal.html",
        context={"metrics": metrics, "records": records},
    )


@router.post("/dev/reset-perfil")
def dev_reset_profile(
    request: Request,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> Any:
    if not dev_reset_enabled():
        raise HTTPException(status_code=404, detail="Not found")
    session_key = _ensure_session_key(request)
    db_module.delete_profile_by_session(conn, session_key)
    request.session.pop("welcome_career", None)
    _draft_clear(request)
    return RedirectResponse(url="/onboarding/paso-1", status_code=303)


@router.post("/perfil")
def create_profile_legacy() -> RedirectResponse:
    """Compatibilidad: el flujo nuevo es por /onboarding/paso-*."""
    return RedirectResponse(url="/onboarding/paso-1", status_code=303)
