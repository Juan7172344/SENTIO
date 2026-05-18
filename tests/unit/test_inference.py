"""Pruebas del motor de inferencia y reglas clínicas."""

from __future__ import annotations

import tempfile
from pathlib import Path

import joblib
import numpy as np
import pytest
from sklearn.tree import DecisionTreeClassifier

from model.clinical_rules import evaluate_clinical_rules
from model.inference import SentioInferenceEngine
from model.preprocessing import FEATURE_COLUMNS, vector_from_user_data


def _minimal_bundle() -> Path:
    rng = np.random.default_rng(0)
    n = 200
    x = rng.normal(size=(n, len(FEATURE_COLUMNS)))
    y = rng.integers(0, 3, size=n)
    clf = DecisionTreeClassifier(max_depth=4, random_state=0)
    clf.fit(x, y)
    fd, path = tempfile.mkstemp(suffix=".joblib")
    import os

    os.close(fd)
    p = Path(path)
    joblib.dump(
        {
            "model": clf,
            "feature_columns": list(FEATURE_COLUMNS),
            "class_names": ["Bajo", "Medio", "Alto"],
        },
        p,
    )
    return p


def test_vector_order_matches_columns() -> None:
    d = {k: float(i + 1) for i, k in enumerate(FEATURE_COLUMNS)}
    v = vector_from_user_data(d)
    assert v.shape == (1, len(FEATURE_COLUMNS))


def test_clinical_stress_over_9() -> None:
    r = evaluate_clinical_rules(
        {
            "age": 20.0,
            "semester": 5.0,
            "habitual_sleep_hours": 8.0,
            "base_academic_stress": 10.0,
            "physical_activity_days_per_week": 3.0,
        }
    )
    assert r.triggered and r.risk_level == "Alto"


def test_clinical_sleep_under_3() -> None:
    r = evaluate_clinical_rules(
        {
            "age": 22.0,
            "semester": 3.0,
            "habitual_sleep_hours": 2.5,
            "base_academic_stress": 4.0,
            "physical_activity_days_per_week": 2.0,
        }
    )
    assert r.triggered and r.risk_level == "Alto"


def test_engine_rules_only_when_missing_file(tmp_path: Path) -> None:
    engine = SentioInferenceEngine(tmp_path / "no_model_here.joblib")
    out = engine.predict_risk(
        {
            "age": 21,
            "semester": 4,
            "habitual_sleep_hours": 7.0,
            "base_academic_stress": 4,
            "physical_activity_days_per_week": 4,
        }
    )
    assert out["source"] == "Clinical"
    assert "confidence" in out


def test_engine_ml_path(tmp_path: Path) -> None:
    artifact = _minimal_bundle()
    try:
        engine = SentioInferenceEngine(artifact)
        engine.warmup()
        out = engine.predict_risk(
            {
                "age": 21.0,
                "semester": 4.0,
                "habitual_sleep_hours": 7.0,
                "base_academic_stress": 5.0,
                "physical_activity_days_per_week": 3.0,
            }
        )
        assert out["source"] == "ML"
        assert out["risk_level"] in ("Bajo", "Medio", "Alto")
    finally:
        artifact.unlink(missing_ok=True)
