# SENTIO

Monitoreo emocional para estudiantes universitarios (FastAPI + ML con scikit-learn).

## Inicio rápido

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m src.ml.train
python -m uvicorn src.main:app --reload --port 8000
```

API de análisis: `POST /analyze` con cuerpo `{"user_id":"<uuid del perfil>"}` (el `user_id` es el campo `id` de `student_profiles`; en el HTML de inicio está en `data-profile-id`).

Abre `http://127.0.0.1:8000/` (te lleva al **onboarding en 3 pasos**). Tras completar el perfil verás el **dashboard** de inicio. Documentación: `http://127.0.0.1:8000/docs`.

## Pruebas

- Automáticas: `pytest tests/ -v`
- Manuales (HTTP real, levanta uvicorn en un puerto libre y recorre el flujo): `python scripts/manual_http_smoke.py` o `make manual-smoke`

### Onboarding otra vez / mensajes de Chrome

- Si **ya creaste un perfil** en este navegador, `/` y `/onboarding` te llevan a **`/inicio`** (historia US-01). No es un fallo.
- Para volver a ver el formulario: ventana de incógnito, borrar cookies del sitio, borrar `data/sentio_local.db`, o en desarrollo define `SENTIO_DEV_RESET=1` y usa el botón en `/inicio` que borra solo tu perfil de prueba.
- La petición **`/.well-known/appspecific/com.chrome.devtools.json`** la hace Chrome con DevTools abierto; la app responde `{}` para no llenar el log de 404.

La arquitectura detallada está en `Architecture.md`; historias de usuario en `user_stories.md`.
