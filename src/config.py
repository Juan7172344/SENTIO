"""Configuración mínima vía variables de entorno (sin dependencias extra)."""

from __future__ import annotations

import os
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def secret_key() -> str:
    key = os.getenv("SENTIO_SECRET_KEY")
    if not key:
        # Solo para desarrollo local; en producción define SENTIO_SECRET_KEY.
        return "sentio-dev-secret-key-change-me-please-32b"
    return key


def database_path() -> Path:
    raw = os.getenv("SENTIO_DATABASE_PATH")
    if raw:
        return Path(raw)
    return project_root() / "data" / "sentio_local.db"


def model_artifact_path() -> Path:
    raw = os.getenv("SENTIO_MODEL_ARTIFACT")
    if raw:
        return Path(raw).expanduser().resolve()
    return project_root() / "model" / "artifacts" / "sentio_model_v1.joblib"


def dev_reset_enabled() -> bool:
    """Si es True, se expone POST /dev/reset-perfil (solo entornos locales de prueba)."""
    return os.getenv("SENTIO_DEV_RESET", "").strip() == "1"
