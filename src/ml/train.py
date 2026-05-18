"""Entrenamiento: dataset sintético alineado con columnas de `student_profiles` + árbol de decisión."""

from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

from model.preprocessing import FEATURE_COLUMNS
from src.config import project_root

CLASS_NAMES = ["Bajo", "Medio", "Alto"]
ARTIFACT_NAME = "sentio_model_v1.joblib"
DATASET_NAME = "sentio_synthetic_bootstrap.csv"


def _project_paths() -> tuple[Path, Path, Path]:
    root = project_root()
    artifacts_dir = root / "model" / "artifacts"
    synthetic_dir = root / "data" / "synthetic"
    return root, artifacts_dir, synthetic_dir


def generate_synthetic_dataset(n_samples: int, seed: int) -> pd.DataFrame:
    """Genera datos sintéticos con las mismas features que el perfil en SQLite."""
    rng = np.random.default_rng(seed)
    age = rng.integers(16, 31, size=n_samples)
    semester = rng.integers(1, 13, size=n_samples)
    habitual_sleep_hours = rng.uniform(4.0, 10.0, size=n_samples)
    base_academic_stress = rng.integers(1, 11, size=n_samples)
    physical_activity_days_per_week = rng.integers(0, 8, size=n_samples)

    age_n = (age.astype(float) - 16.0) / 14.0
    sem_n = (semester.astype(float) - 1.0) / 11.0
    sleep_n = (habitual_sleep_hours - 4.0) / 6.0
    stress_n = (base_academic_stress.astype(float) - 1.0) / 9.0
    ex_n = physical_activity_days_per_week.astype(float) / 7.0

    combined = (
        0.32 * stress_n
        + 0.28 * (1.0 - sleep_n)
        + 0.18 * (1.0 - ex_n)
        + 0.12 * age_n * 0.4
        + 0.10 * sem_n * 0.3
        + rng.normal(0.0, 0.07, size=n_samples)
    )
    combined = np.clip(combined, 0.0, 1.0)

    risk = np.zeros(n_samples, dtype=int)
    risk[combined < 0.34] = 0
    risk[(combined >= 0.34) & (combined < 0.67)] = 1
    risk[combined >= 0.67] = 2

    flip_mask = rng.random(n_samples) < 0.06
    risk[flip_mask] = rng.integers(0, 3, size=int(flip_mask.sum()))

    return pd.DataFrame(
        {
            "age": age,
            "semester": semester,
            "habitual_sleep_hours": habitual_sleep_hours,
            "base_academic_stress": base_academic_stress,
            "physical_activity_days_per_week": physical_activity_days_per_week,
            "risk_level": risk,
        }
    )


def train_and_persist(df: pd.DataFrame, artifacts_dir: Path) -> Path:
    x = df[list(FEATURE_COLUMNS)].to_numpy(dtype=float)
    y = df["risk_level"].to_numpy(dtype=int)

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42, stratify=y
    )

    model = DecisionTreeClassifier(
        max_depth=8,
        min_samples_leaf=8,
        class_weight="balanced",
        random_state=42,
    )
    model.fit(x_train, y_train)

    y_pred = model.predict(x_test)
    print(classification_report(y_test, y_pred, target_names=CLASS_NAMES))

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifacts_dir / ARTIFACT_NAME
    bundle = {
        "model": model,
        "feature_columns": list(FEATURE_COLUMNS),
        "class_names": list(CLASS_NAMES),
    }
    joblib.dump(bundle, artifact_path)
    return artifact_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrena modelo SENTIO alineado al perfil SQLite.")
    parser.add_argument("--samples", type=int, default=1500, help="Número de filas sintéticas.")
    parser.add_argument("--seed", type=int, default=42, help="Semilla reproducible.")
    args = parser.parse_args()

    _, artifacts_dir, synthetic_dir = _project_paths()
    synthetic_dir.mkdir(parents=True, exist_ok=True)

    df = generate_synthetic_dataset(args.samples, args.seed)
    csv_path = synthetic_dir / DATASET_NAME
    df.to_csv(csv_path, index=False)

    artifact_path = train_and_persist(df, artifacts_dir)
    print(f"Dataset guardado en: {csv_path}")
    print(f"Modelo guardado en: {artifact_path}")


if __name__ == "__main__":
    main()
