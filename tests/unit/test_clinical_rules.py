"""Pruebas del módulo de reglas clínicas."""

from __future__ import annotations

from model.clinical_rules import evaluate_clinical_rules


def test_no_trigger_on_balanced_inputs() -> None:
    r = evaluate_clinical_rules(
        {
            "age": 20.0,
            "semester": 4.0,
            "habitual_sleep_hours": 7.5,
            "base_academic_stress": 5.0,
            "physical_activity_days_per_week": 3.0,
        }
    )
    assert r.triggered is False
