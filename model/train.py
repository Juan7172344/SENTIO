"""Punto de entrada de entrenamiento del monorepo: ejecuta `python -m src.ml.train` desde la raíz del repo."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    raise SystemExit(
        subprocess.call(
            [sys.executable, "-m", "src.ml.train", *sys.argv[1:]],
            cwd=str(root),
        )
    )
