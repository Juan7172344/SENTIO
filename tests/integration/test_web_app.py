"""Pruebas de integración del flujo web US-01 (sesión + SQLite + Jinja2)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "sentio_test.db"
    art_dir = tmp_path / "artifacts"
    art_dir.mkdir(parents=True)
    model_file = art_dir / "sentio_model_v1.joblib"
    monkeypatch.setenv("SENTIO_DATABASE_PATH", str(db_path))
    monkeypatch.setenv("SENTIO_MODEL_ARTIFACT", str(model_file))
    monkeypatch.setenv("SENTIO_SECRET_KEY", "test-secret-key-at-least-32-chars-long")

    from src.ml.train import generate_synthetic_dataset, train_and_persist

    train_and_persist(generate_synthetic_dataset(250, 7), art_dir)

    from src.main import create_app

    app = create_app()
    with TestClient(app) as test_client:
        test_client.sentio_db_path = db_path  # type: ignore[attr-defined]
        yield test_client


def test_root_redirects_to_onboarding_paso1(client: TestClient) -> None:
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/onboarding/paso-1"


def test_onboarding_paso1_renders(client: TestClient) -> None:
    response = client.get("/onboarding/paso-1")
    assert response.status_code == 200
    assert "Paso 1 de 3" in response.text
    assert "Continuar" in response.text
    assert 'name="career"' in response.text


def test_validation_empty_career(client: TestClient) -> None:
    response = client.post(
        "/onboarding/paso-1",
        data={"age": 20, "career": "   ", "semester": 3},
    )
    assert response.status_code == 422
    assert "obligatoria" in response.text


def _complete_onboarding(client: TestClient) -> None:
    assert client.post(
        "/onboarding/paso-1",
        data={"age": 21, "career": "Ingeniería de Sistemas", "semester": 4},
        follow_redirects=False,
    ).status_code == 303
    assert client.post(
        "/onboarding/paso-2",
        data={"habitual_sleep_hours": 6.5, "base_academic_stress": 7},
        follow_redirects=False,
    ).status_code == 303
    assert client.post(
        "/onboarding/paso-3",
        data={"physical_activity_days_per_week": 2},
        follow_redirects=False,
    ).status_code == 303


def test_create_profile_and_home_redirect(client: TestClient) -> None:
    _complete_onboarding(client)

    home = client.get("/inicio", follow_redirects=True)
    assert home.status_code == 200
    assert "Ingeniería de Sistemas" in home.text
    assert "SENTIO" in home.text
    assert "Perfil creado" in home.text
    assert "Registrar hoy" in home.text
    assert "Evaluación orientativa" in home.text
    assert "Confianza (score)" in home.text


def test_post_analyze_returns_json(client: TestClient) -> None:
    _complete_onboarding(client)
    db_path = client.sentio_db_path  # type: ignore[attr-defined]
    import sqlite3

    row = sqlite3.connect(str(db_path)).execute("SELECT id FROM student_profiles LIMIT 1").fetchone()
    assert row is not None
    uid = row[0]
    res = client.post("/analyze", json={"user_id": uid})
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == uid
    assert "risk_level" in data
    assert "confidence_score" in data
    assert "disclaimer" in data


def test_onboarding_redirects_when_profile_exists(client: TestClient) -> None:
    _complete_onboarding(client)

    response = client.get("/onboarding", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/inicio"


def test_static_css_served(client: TestClient) -> None:
    response = client.get("/static/css/sentio.css")
    assert response.status_code == 200
    assert b"sentio-shell" in response.content


def test_openapi_docs_available(client: TestClient) -> None:
    response = client.get("/docs")
    assert response.status_code == 200


def test_chrome_devtools_well_known(client: TestClient) -> None:
    response = client.get("/.well-known/appspecific/com.chrome.devtools.json")
    assert response.status_code == 200
    assert response.json() == {}


def test_favicon_is_no_content(client: TestClient) -> None:
    assert client.get("/favicon.ico").status_code == 204


def test_dev_reset_profile_not_found_when_disabled(monkeypatch, client: TestClient) -> None:
    monkeypatch.delenv("SENTIO_DEV_RESET", raising=False)
    assert client.post("/dev/reset-perfil").status_code == 404


def test_dev_reset_profile_clears_and_shows_onboarding(monkeypatch, client: TestClient) -> None:
    monkeypatch.setenv("SENTIO_DEV_RESET", "1")
    _complete_onboarding(client)
    reset = client.post("/dev/reset-perfil", follow_redirects=False)
    assert reset.status_code == 303
    assert reset.headers["location"] == "/onboarding/paso-1"
    page = client.get("/onboarding/paso-1")
    assert page.status_code == 200
    assert "Paso 1 de 3" in page.text
