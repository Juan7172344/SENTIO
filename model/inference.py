"""Motor de inferencia: reglas clínicas + ML (carga diferida del artefacto)."""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any, Optional

import joblib
import numpy as np

from model.clinical_rules import evaluate_clinical_rules
from model.preprocessing import FEATURE_COLUMNS, vector_from_user_data

logger = logging.getLogger(__name__)

CLASS_NAMES_DEFAULT = ("Bajo", "Medio", "Alto")


class SentioInferenceEngine:
    """Evalúa riesgo emocional orientativo: primero reglas, luego árbol entrenado."""

    def __init__(self, artifact_path: Path) -> None:
        self._artifact_path = Path(artifact_path)
        self._lock = threading.Lock()
        self._bundle: Optional[dict[str, Any]] = None
        self._model = None
        self._class_names: tuple[str, ...] = CLASS_NAMES_DEFAULT
        self._feature_columns: list[str] = list(FEATURE_COLUMNS)
        self.ml_available = self._artifact_path.is_file()
        if not self.ml_available:
            logger.warning(
                "Artefacto ML no encontrado en %s. Modo solo reglas clínicas + heurística.",
                self._artifact_path,
            )

    def warmup(self) -> None:
        """Precarga el artefacto en el arranque si está disponible."""
        self._ensure_model_loaded()

    def _ensure_model_loaded(self) -> None:
        if not self.ml_available:
            return
        with self._lock:
            if self._model is not None:
                return
            try:
                bundle = joblib.load(self._artifact_path)
            except Exception as exc:
                logger.warning("No se pudo cargar el modelo: %s. Modo solo reglas.", exc)
                self.ml_available = False
                return
            self._bundle = bundle
            self._model = bundle.get("model")
            self._class_names = tuple(bundle.get("class_names", CLASS_NAMES_DEFAULT))
            cols = bundle.get("feature_columns")
            if cols is not None:
                self._feature_columns = list(cols)
            if self._model is None:
                self.ml_available = False
                logger.warning("Bundle sin 'model' válido; modo solo reglas.")

    def predict_risk(self, user_data: dict[str, float | int]) -> dict[str, Any]:
        """
        Retorna análisis orientativo.
        Claves: risk (bool), risk_level (str), confidence (float),
        source ('Clinical' | 'ML'), message (str).
        """
        normalized = {k: float(user_data[k]) for k in FEATURE_COLUMNS}

        clinical = evaluate_clinical_rules(normalized)
        if clinical.triggered and clinical.risk_level:
            return {
                "risk": clinical.risk_level in ("Medio", "Alto"),
                "risk_level": clinical.risk_level,
                "confidence": 1.0,
                "source": "Clinical",
                "message": clinical.message,
            }

        self._ensure_model_loaded()
        if self._model is None:
            return self._heuristic_without_ml(normalized)

        vec = vector_from_user_data(normalized)
        if vec.shape[1] != len(self._feature_columns):
            logger.warning(
                "Dimensiones de features no coinciden con el modelo; usando heurística."
            )
            return self._heuristic_without_ml(normalized)

        proba = self._model.predict_proba(vec)[0]
        idx = int(np.argmax(proba))
        level = self._class_names[idx] if idx < len(self._class_names) else self._class_names[0]
        conf = float(proba[idx])
        return {
            "risk": level in ("Medio", "Alto"),
            "risk_level": level,
            "confidence": round(conf, 3),
            "source": "ML",
            "message": self._message_for_ml(level, conf),
        }

    def _message_for_ml(self, level: str, confidence: float) -> str:
        if level == "Bajo":
            return f"Indicadores mayormente favorables (confianza del modelo {confidence:.0%})."
        if level == "Medio":
            return f"Hay señales a vigilar; conviene mantener hábitos saludables (confianza {confidence:.0%})."
        return f"Se detectan factores de riesgo elevados; prioriza descanso y apoyo (confianza {confidence:.0%})."

    def _heuristic_without_ml(self, u: dict[str, float]) -> dict[str, Any]:
        stress = u["base_academic_stress"]
        sleep = u["habitual_sleep_hours"]
        ex = u["physical_activity_days_per_week"]
        if stress >= 8 or sleep < 5:
            level = "Medio"
            msg = "Modelo ML no disponible; evaluación conservadora por reglas ampliadas."
        elif stress >= 6 and ex <= 2:
            level = "Medio"
            msg = "Modelo ML no disponible; estrés moderado y poca actividad física."
        else:
            level = "Bajo"
            msg = "Modelo ML no disponible; sin señales críticas en la evaluación heurística."
        return {
            "risk": level in ("Medio", "Alto"),
            "risk_level": level,
            "confidence": 0.55 if level == "Medio" else 0.45,
            "source": "Clinical",
            "message": msg,
        }
