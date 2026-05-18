"""Reglas heurísticas de prioridad (antes del ML)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ClinicalEvaluation:
    triggered: bool
    risk_level: Optional[str]
    message: str


def evaluate_clinical_rules(user_data: dict[str, float | int]) -> ClinicalEvaluation:
    stress = float(user_data.get("base_academic_stress", 0))
    sleep = float(user_data.get("habitual_sleep_hours", 8.0))

    if stress > 9:
        return ClinicalEvaluation(
            triggered=True,
            risk_level="Alto",
            message="Estrés base muy elevado; se aplica evaluación prioritaria.",
        )
    if sleep < 3:
        return ClinicalEvaluation(
            triggered=True,
            risk_level="Alto",
            message="Sueño habitual extremadamente bajo; se aplica evaluación prioritaria.",
        )
    return ClinicalEvaluation(triggered=False, risk_level=None, message="")
