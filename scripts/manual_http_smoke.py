"""
Pruebas «manuales» automatizadas contra un servidor HTTP real (mismo flujo que en el navegador).

Uso:
    python scripts/manual_http_smoke.py

Opcional:
    set SENTIO_MANUAL_PORT=8765
    set SENTIO_DATABASE_PATH=C:\\ruta\\manual_smoke.db
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Callable

import httpx

ROOT = Path(__file__).resolve().parents[1]


def _wait_until(predicate: Callable[[], bool], timeout_s: float = 20.0, interval_s: float = 0.25) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval_s)
    return False


def main() -> int:
    port = int(os.environ.get("SENTIO_MANUAL_PORT", "8765"))
    base = f"http://127.0.0.1:{port}"

    own_db = False
    if os.environ.get("SENTIO_DATABASE_PATH"):
        db_path = os.environ["SENTIO_DATABASE_PATH"]
    else:
        db_fd, db_path = tempfile.mkstemp(prefix="sentio_manual_", suffix=".db")
        os.close(db_fd)
        own_db = True
    try:
        env = os.environ.copy()
        env["SENTIO_DATABASE_PATH"] = db_path
        env["SENTIO_SECRET_KEY"] = os.environ.get(
            "SENTIO_SECRET_KEY", "manual-smoke-secret-key-32chars-min"
        )

        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "src.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ]
        proc = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        print("=" * 60)
        print("PRUEBAS MANUALES (HTTP real, cookies de sesion)")
        print(f"Servidor: {base}")
        print(f"BD temporal: {env['SENTIO_DATABASE_PATH']}")
        print("=" * 60)

        def server_up() -> bool:
            try:
                r = httpx.get(base + "/onboarding/paso-1", timeout=1.0)
                return r.status_code == 200
            except httpx.RequestError:
                return False

        if not _wait_until(server_up, timeout_s=25.0):
            proc.terminate()
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill()
            print("ERROR: el servidor no respondió a tiempo.")
            return 1

        steps: list[tuple[str, bool, str]] = []

        with httpx.Client(base_url=base, timeout=10.0) as client:
            r0 = client.get("/", follow_redirects=False)
            ok0 = r0.status_code == 303 and r0.headers.get("location") == "/onboarding/paso-1"
            steps.append(("0) GET / - redirige a paso 1", ok0, f"status={r0.status_code}"))

            r1 = client.get("/onboarding/paso-1")
            ok1 = r1.status_code == 200 and "Paso 1 de 3" in r1.text
            steps.append(("1) GET paso-1 - onboarding", ok1, f"status={r1.status_code}"))

            r2 = client.post(
                "/onboarding/paso-1",
                data={"age": 20, "career": "   ", "semester": 3},
            )
            ok2 = r2.status_code == 422 and "obligatoria" in r2.text
            steps.append(("2) POST paso-1 - carrera vacia", ok2, f"status={r2.status_code}"))

            assert client.post(
                "/onboarding/paso-1",
                data={"age": 22, "career": "Psicología", "semester": 5},
                follow_redirects=False,
            ).status_code == 303
            assert client.post(
                "/onboarding/paso-2",
                data={"habitual_sleep_hours": 6.25, "base_academic_stress": 6},
                follow_redirects=False,
            ).status_code == 303
            r3 = client.post(
                "/onboarding/paso-3",
                data={"physical_activity_days_per_week": 2},
                follow_redirects=False,
            )
            ok3 = r3.status_code == 303 and r3.headers.get("location") == "/inicio"
            steps.append(
                (
                    "3) POST paso-1,2,3 - perfil creado",
                    ok3,
                    f"status={r3.status_code} location={r3.headers.get('location')!r}",
                )
            )

            r4 = client.get("/inicio")
            ok4 = r4.status_code == 200 and "Psicología" in r4.text and "SENTIO" in r4.text
            steps.append(("4) GET /inicio - dashboard", ok4, f"status={r4.status_code}"))

            r5 = client.get("/onboarding/paso-1", follow_redirects=False)
            ok5 = r5.status_code == 303 and r5.headers.get("location") == "/inicio"
            steps.append(
                (
                    "5) GET paso-1 con perfil - redirige a inicio",
                    ok5,
                    f"status={r5.status_code} location={r5.headers.get('location')!r}",
                )
            )

            r6 = client.get("/docs")
            ok6 = r6.status_code == 200
            steps.append(("6) GET /docs - OpenAPI", ok6, f"status={r6.status_code}"))

        for label, ok, detail in steps:
            mark = "OK" if ok else "FALLO"
            print(f"[{mark}] {label}")
            print(f"       {detail}")

        all_ok = all(s[1] for s in steps)
        print("=" * 60)
        print("Resumen:", "TODAS OK" if all_ok else "HUBO FALLOS")
        print("=" * 60)

        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()

        return 0 if all_ok else 2
    finally:
        if own_db:
            try:
                if os.path.exists(db_path):
                    os.remove(db_path)
            except OSError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
