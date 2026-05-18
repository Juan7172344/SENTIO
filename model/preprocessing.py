"""Orden y extracción de features alineados con la tabla `student_profiles` y el entrenamiento."""

from __future__ import annotations

import numpy as np

FEATURE_COLUMNS: list[str] = [
    "age",
    "semester",
    "habitual_sleep_hours",
    "base_academic_stress",
    "physical_activity_days_per_week",
]


def vector_from_user_data(user_data: dict[str, float | int]) -> np.ndarray:
    """Construye una fila (1, n_features) en el mismo orden que el entrenamiento."""
    missing = [c for c in FEATURE_COLUMNS if c not in user_data]
    if missing:
        raise ValueError(f"Faltan claves en user_data: {missing}")
    return np.array(
        [[float(user_data[c]) for c in FEATURE_COLUMNS]],
        dtype=np.float64,
    )
