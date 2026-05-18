# Architecture.md — SENTIO: Sistema de Monitoreo del Bienestar Emocional Estudiantil

> **Versión:** 1.0.0 · **Fecha:** Mayo 2026  
> **Autores:** Juan Andrés Suárez Fonseca · Valeria Bermúdez Aguilar  
> **Institución:** Escuela Colombiana de Ingeniería Julio Garavito  
> **Curso:** Principios y Tecnologías de Inteligencia Artificial — Grupo 3

---

## 1. Visión General de la Arquitectura

SENTIO sigue una arquitectura **monorepo de tres capas** con separación estricta de responsabilidades entre el motor de datos/ML, la capa de negocio (API) y la interfaz de usuario. El sistema implementa un pipeline de aprendizaje supervisado que clasifica el nivel de riesgo emocional de un estudiante (Bajo / Medio / Alto) a partir de registros diarios estructurados.

```
┌────────────────────────────────────────────────────────────────┐
│                        SENTIO Monorepo                         │
│                                                                │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────────┐ │
│  │ /frontend│◄──►│    /api      │◄──►│   /model  +  /data   │ │
│  │ Streamlit│    │   FastAPI    │    │  Scikit-learn / PT   │ │
│  └──────────┘    └──────────────┘    └──────────────────────┘ │
│                         │                                      │
│                  ┌──────┴──────┐                               │
│                  │  SQLite /   │                               │
│                  │  PostgreSQL │                               │
│                  └─────────────┘                               │
└────────────────────────────────────────────────────────────────┘
```

**Principios de diseño:**

- **Separación de capas:** El modelo de ML nunca se invoca directamente desde el frontend; toda comunicación pasa por la API REST.
- **Reglas deterministas primero:** Antes de invocar el modelo estadístico, un motor de reglas clínicas evalúa condiciones críticas (sueño < 5h, cambio abrupto), garantizando seguridad del usuario.
- **Confianza explícita:** Toda predicción incluye un `confidence_score` y un `data_quality_flag` que se exponen al usuario.
- **Privacidad por diseño:** Los datos de salud mental se tratan como datos sensibles (Ley 1581/2012 Colombia); cifrado en reposo y HTTPS obligatorio.

---

## 2. Árbol de Directorios (Monorepo)

```
sentio/
│
├── README.md
├── Architecture.md                  # Este documento
├── .env.example                     # Variables de entorno (nunca commitear .env)
├── .gitignore
├── docker-compose.yml               # Orquestación local (API + DB)
├── pyproject.toml                   # Dependencias unificadas (uv / poetry)
├── Makefile                         # Comandos de desarrollo frecuentes
│
├── data/                            # Capa de datos — todo lo relacionado con datasets
│   ├── raw/                         # Datos originales, nunca modificar
│   │   └── student_mental_health_reference.csv   # Dataset de referencia (Kaggle/UCI)
│   ├── synthetic/                   # Datos generados para entrenamiento
│   │   ├── generator.py             # Script de generación de datos sintéticos
│   │   └── sentio_synthetic_v1.csv  # Dataset sintético generado (1000+ registros)
│   ├── processed/                   # Salidas del preprocesamiento
│   │   ├── X_train.npy
│   │   ├── X_test.npy
│   │   ├── y_train.npy
│   │   └── y_test.npy
│   └── schemas/
│       └── daily_record_schema.py   # Pydantic schema del registro diario (fuente de verdad)
│
├── model/                           # Capa de ML — pipeline completo
│   ├── __init__.py
│   ├── config.py                    # Hiperparámetros y constantes del modelo
│   ├── preprocessing.py             # Limpieza, feature engineering, escalado
│   ├── train.py                     # Script principal de entrenamiento
│   ├── evaluate.py                  # Métricas, matriz de confusión, curvas ROC
│   ├── inference.py                 # Función predict() para uso en la API
│   ├── clinical_rules.py            # Motor de reglas deterministas de prioridad clínica
│   ├── artifacts/                   # Modelos entrenados serializados
│   │   ├── sentio_model_v1.joblib   # Modelo principal (Random Forest)
│   │   ├── scaler_v1.joblib         # StandardScaler entrenado
│   │   └── label_encoder_v1.joblib  # LabelEncoder de clases de riesgo
│   └── notebooks/                   # Exploración y experimentación
│       ├── 01_eda.ipynb             # Análisis exploratorio de datos
│       ├── 02_feature_engineering.ipynb
│       ├── 03_model_selection.ipynb # Comparación de algoritmos
│       └── 04_evaluation_report.ipynb
│
├── api/                             # Capa de negocio — FastAPI
│   ├── __init__.py
│   ├── main.py                      # Punto de entrada FastAPI, configuración CORS
│   ├── dependencies.py              # Inyección de dependencias (DB session, modelo)
│   ├── routers/
│   │   ├── records.py               # POST /records · GET /records/{user_id}
│   │   ├── analysis.py              # GET /analysis/{user_id} · GET /analysis/{user_id}/weekly
│   │   ├── recommendations.py       # GET /recommendations/{user_id}
│   │   └── health.py                # GET /health (liveness probe)
│   ├── schemas/
│   │   ├── record.py                # Pydantic models para request/response de registros
│   │   ├── analysis.py              # Pydantic models para resultados de análisis
│   │   └── recommendation.py        # Pydantic models para recomendaciones
│   ├── services/
│   │   ├── record_service.py        # Lógica de negocio: validación, persistencia
│   │   ├── analysis_service.py      # Orquesta reglas clínicas + modelo ML
│   │   └── recommendation_service.py
│   ├── db/
│   │   ├── database.py              # Configuración SQLAlchemy (SQLite dev / PG prod)
│   │   ├── models.py                # ORM models: User, DailyRecord, RiskAssessment
│   │   └── migrations/              # Alembic migrations
│   └── middleware/
│       ├── auth.py                  # JWT simple (sin dependencias externas de auth)
│       └── rate_limit.py            # Throttling por usuario
│
├── frontend/                        # Capa de presentación — Streamlit
│   ├── app.py                       # Punto de entrada Streamlit
│   ├── pages/
│   │   ├── 01_registro_diario.py    # Formulario de registro
│   │   ├── 02_mi_analisis.py        # Dashboard de análisis semanal
│   │   ├── 03_recomendaciones.py    # Tarjetas de recomendaciones
│   │   └── 04_historial.py          # Gráficas de tendencia
│   ├── components/
│   │   ├── risk_badge.py            # Componente visual del nivel de riesgo
│   │   ├── trend_chart.py           # Gráfica de tendencia semanal (Plotly)
│   │   └── mood_selector.py         # Selector visual de estado de ánimo
│   └── utils/
│       ├── api_client.py            # Cliente HTTP para la API (httpx)
│       └── session.py               # Gestión de estado de sesión Streamlit
│
├── tests/                           # Suite de pruebas
│   ├── unit/
│   │   ├── test_preprocessing.py
│   │   ├── test_clinical_rules.py   # Pruebas de casos borde críticos (EC-01 a EC-10)
│   │   └── test_inference.py
│   ├── integration/
│   │   ├── test_api_records.py
│   │   └── test_api_analysis.py
│   └── fixtures/
│       └── sample_records.py        # Datos de prueba reutilizables
│
├── scripts/
│   ├── generate_data.py             # Entry point: python scripts/generate_data.py
│   ├── train_model.py               # Entry point: python scripts/train_model.py
│   └── seed_db.py                   # Población inicial de la base de datos (dev)
│
└── docs/
    ├── api_reference.md             # Documentación de endpoints (auto-generada con /docs)
    ├── data_dictionary.md           # Definición de variables y escalas
    └── ethics_note.md               # Nota ética y limitaciones clínicas
```

---

## 3. Stack Tecnológico

### 3.1 Back-end y API

| Componente | Tecnología | Versión | Justificación |
|---|---|---|---|
| Framework API | **FastAPI** | ≥0.111 | Tipado nativo con Pydantic, documentación automática OpenAPI/Swagger, rendimiento async, ideal para servir modelos ML |
| Servidor ASGI | **Uvicorn** | ≥0.29 | Worker ASGI de alto rendimiento, compatible con FastAPI |
| ORM | **SQLAlchemy** | ≥2.0 | Soporte async, compatible con SQLite (dev) y PostgreSQL (prod) |
| Migraciones | **Alembic** | ≥1.13 | Gestión de esquemas de DB versionada |
| Validación | **Pydantic v2** | ≥2.7 | Validación de entrada/salida con tipado estricto, integrado en FastAPI |
| Auth | **PyJWT** | ≥2.8 | Tokens JWT livianos sin dependencias externas de auth complejas |

```python
# api/main.py — Estructura base
from fastapi import FastAPI
from api.routers import records, analysis, recommendations, health
from api.middleware.rate_limit import RateLimitMiddleware

app = FastAPI(
    title="SENTIO API",
    description="Sistema de Monitoreo del Bienestar Emocional Estudiantil",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(RateLimitMiddleware, max_requests=60, window_seconds=60)

app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(records.router, prefix="/records", tags=["Records"])
app.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
```

### 3.2 Machine Learning

| Componente | Tecnología | Versión | Justificación |
|---|---|---|---|
| Framework ML principal | **Scikit-learn** | ≥1.5 | Madurez, amplia documentación, implementaciones robustas de Random Forest, regresión logística y pipelines |
| Manipulación de datos | **Pandas** | ≥2.2 | Estándar de facto para manipulación de DataFrames tabulares estructurados |
| Álgebra lineal | **NumPy** | ≥1.26 | Base numérica de todo el stack de ML |
| Serialización de modelos | **Joblib** | ≥1.4 | Serialización eficiente de modelos Scikit-learn con soporte de memoria mapeada |
| Generación de datos sintéticos | **Faker + NumPy** | - | Generación controlada de datos con distribuciones realistas para entrenamiento |
| Visualización ML | **Matplotlib / Seaborn** | ≥3.9 / ≥0.13 | Curvas ROC, matrices de confusión, distribuciones de features |
| Experimentos (opcional) | **MLflow** | ≥2.13 | Tracking de experimentos, comparación de modelos, registro de artefactos |

> **Nota sobre PyTorch:** Dado que el dataset es tabular y estructurado (no imágenes ni texto), Scikit-learn es la elección óptima para el prototipo académico. PyTorch se reserva como extensión futura si se incorporan datos de texto libre (diarios personales) que requieran procesamiento NLP con modelos de embeddings.

### 3.3 Front-end / Prototipado

| Componente | Tecnología | Versión | Justificación |
|---|---|---|---|
| Framework UI | **Streamlit** | ≥1.35 | Prototipado rápido en Python puro sin necesidad de JavaScript, ideal para contexto académico |
| Gráficas interactivas | **Plotly** | ≥5.22 | Gráficas de tendencia temporal interactivas, soporte nativo en Streamlit |
| Cliente HTTP | **HTTPX** | ≥0.27 | Cliente HTTP async, reemplaza requests con soporte HTTP/2 |

### 3.4 Base de Datos

| Entorno | Motor | Justificación |
|---|---|---|
| Desarrollo local | **SQLite** | Sin instalación, persistencia en archivo, ideal para desarrollo y pruebas |
| Producción / staging | **PostgreSQL ≥16** | Concurrencia, confiabilidad, soporte nativo en SQLAlchemy async |

### 3.5 Infraestructura y DevOps

| Componente | Tecnología | Justificación |
|---|---|---|
| Contenedores | **Docker + Docker Compose** | Reproducibilidad del entorno, facilita despliegue |
| Gestión de dependencias | **uv** (o Poetry) | Resolución rápida de dependencias, lockfile determinista |
| Testing | **Pytest + pytest-asyncio** | Cobertura de unit e integration tests, soporte async |
| Variables de entorno | **python-dotenv** | Gestión segura de secretos y configuración por entorno |
| Linting / Formato | **Ruff + Black** | Calidad de código uniforme |

---

## 4. Pipeline de ML — Descripción Detallada

El pipeline sigue cuatro etapas secuenciales desde la generación de datos hasta la inferencia en tiempo real.

### Etapa 1: Generación y Preprocesamiento de Datos

```
data/synthetic/generator.py
        │
        ▼
data/synthetic/sentio_synthetic_v1.csv
        │
        ▼
model/preprocessing.py  ──►  data/processed/{X,y}_{train,test}.npy
```

**Dataset:** Se utiliza un dataset sintético generado con distribuciones estadísticamente coherentes con la literatura de salud mental estudiantil (Gómez et al., 2022). Cada registro representa una ventana de 7 días de un estudiante.

**Variables de entrada (features por ventana de 7 días):**

```python
# model/preprocessing.py — Feature set completo
FEATURE_COLUMNS = [
    # Promedios de la ventana
    "avg_mood",           # Promedio ánimo (1-5)
    "avg_energy",         # Promedio energía (1-5)
    "avg_sleep_hours",    # Promedio horas de sueño
    "avg_stress",         # Promedio estrés (1-10)

    # Variabilidad (desviación estándar)
    "std_mood",
    "std_energy",
    "std_sleep_hours",
    "std_stress",

    # Tendencia (pendiente de regresión lineal sobre 7 días)
    "trend_mood",         # Positivo = mejora, negativo = deterioro
    "trend_stress",

    # Deltas críticos
    "max_daily_mood_drop",    # Máxima caída de ánimo en un solo día (EC-08)
    "days_sleep_below_5h",    # Días con sueño < 5h en la ventana (EC-04)
    "days_stress_above_8",    # Días con estrés ≥ 8/10

    # Actividades (frecuencia en 7 días)
    "exercise_days",
    "social_days",
    "study_days",
    "rest_days",

    # Metadatos
    "days_registered",        # Cantidad de días con registro (calidad de datos)
    "has_retroactive_flag",   # Flag de registros retroactivos (EC-05)
]

TARGET_COLUMN = "risk_level"  # 0=Bajo, 1=Medio, 2=Alto
```

**Pasos de preprocesamiento:**

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer

preprocessing_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),  # Manejo de días sin registro
    ("scaler", StandardScaler()),                   # Normalización z-score
])
```

### Etapa 2: Entrenamiento

```python
# model/train.py — Flujo principal de entrenamiento
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, GridSearchCV
import joblib

# Modelo principal: Random Forest
# Justificación:
#   - Robusto ante features no lineales (correlación sueño-estrés)
#   - Produce feature importances interpretables (explainability clínica)
#   - Maneja bien clases desbalanceadas con class_weight='balanced'
#   - No requiere suposición de normalidad en los datos

rf_params = {
    "n_estimators": [100, 200, 300],
    "max_depth": [5, 10, 15, None],
    "min_samples_leaf": [2, 5, 10],
    "class_weight": ["balanced"],
    "random_state": [42],
}

model = GridSearchCV(
    estimator=RandomForestClassifier(),
    param_grid=rf_params,
    cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
    scoring="f1_macro",     # Métrica principal: F1 macro (clases desbalanceadas)
    n_jobs=-1,
    verbose=1,
)

model.fit(X_train, y_train)
joblib.dump(model.best_estimator_, "model/artifacts/sentio_model_v1.joblib")
```

**Modelos evaluados en `notebooks/03_model_selection.ipynb`:**

| Modelo | Ventaja | Desventaja |
|---|---|---|
| **Random Forest** ✓ | Robusto, interpretable, maneja no-linealidades | Lento en predicción con muchos árboles |
| Regresión Logística | Muy interpretable, rápido | Asume linealidad entre features y target |
| Gradient Boosting | Alta precisión | Propenso a overfitting, lento en entrenamiento |
| SVM (RBF kernel) | Bueno en alta dimensionalidad | Caja negra, difícil de calibrar |

### Etapa 3: Evaluación

```python
# model/evaluate.py — Métricas completas
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    f1_score,
)

# Objetivo del proyecto: Precisión ≥ 80% (definido en Hito 1)
# Métrica prioritaria: Recall en clase "Alto" — minimizar falsos negativos clínicos

def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    report = {
        "classification_report": classification_report(
            y_test, y_pred, target_names=["Bajo", "Medio", "Alto"]
        ),
        "f1_macro": f1_score(y_test, y_pred, average="macro"),
        "roc_auc_ovr": roc_auc_score(y_test, y_proba, multi_class="ovr"),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        # Métrica de seguridad: falsos negativos en clase "Alto"
        "alto_recall": classification_report(
            y_test, y_pred, output_dict=True
        )["Alto"]["recall"],
    }
    return report

# Umbral de aceptación de seguridad:
# - Recall "Alto" >= 0.85  (nunca perder un caso de riesgo real)
# - F1 macro >= 0.80
# - Tiempo de inferencia < 100ms por predicción
```

### Etapa 4: Inferencia via API

```python
# model/clinical_rules.py — Motor de reglas deterministas (ejecuta ANTES del modelo)
from dataclasses import dataclass
from typing import Optional

@dataclass
class ClinicalRuleResult:
    triggered: bool
    forced_risk_level: Optional[str]   # Sobrescribe al modelo si se activa
    rule_code: Optional[str]
    explanation: str

def evaluate_clinical_rules(features: dict) -> ClinicalRuleResult:
    """
    Reglas de dominancia clínica que garantizan seguridad del usuario.
    Ejecutan antes del modelo estadístico y pueden forzar la clasificación.
    """
    # EC-08: Deterioro súbito severo
    if features.get("max_daily_mood_drop", 0) >= 2 and features.get("avg_stress", 0) >= 4:
        return ClinicalRuleResult(
            triggered=True, forced_risk_level="Alto",
            rule_code="CRITICAL_ACUTE_DROP",
            explanation="Caída abrupta en ánimo con estrés elevado detectada."
        )

    # EC-04: Privación de sueño severa
    if features.get("days_sleep_below_5h", 0) >= 3:
        return ClinicalRuleResult(
            triggered=True, forced_risk_level="Medio",
            rule_code="SLEEP_DEPRIVATION",
            explanation="Privación de sueño sostenida (≥3 días bajo 5h)."
        )

    # EC-02: Contradicción ánimo-sueño
    if (features.get("avg_mood", 5) >= 4 and
        features.get("avg_stress", 0) >= 4 and
        features.get("avg_sleep_hours", 8) <= 4):
        return ClinicalRuleResult(
            triggered=True, forced_risk_level="Medio",
            rule_code="CONTRADICTORY_SIGNALS",
            explanation="Ánimo alto con privación de sueño y estrés elevado: señal contradictoria."
        )

    return ClinicalRuleResult(triggered=False, forced_risk_level=None,
                              rule_code=None, explanation="Sin reglas clínicas activadas.")


# model/inference.py — Función de predicción completa
import joblib
import numpy as np

_model = joblib.load("model/artifacts/sentio_model_v1.joblib")
_scaler = joblib.load("model/artifacts/scaler_v1.joblib")

RISK_LABELS = {0: "Bajo", 1: "Medio", 2: "Alto"}

def predict_risk(features: dict, days_registered: int) -> dict:
    """
    Retorna clasificación de riesgo con nivel de confianza y flags de calidad.
    """
    # Validación de calidad de datos
    data_quality_flag = "ok"
    if days_registered < 5:
        data_quality_flag = "insufficient_data"
    if features.get("has_retroactive_flag"):
        data_quality_flag = "retroactive_records"

    # Capa 1: Reglas clínicas deterministas
    clinical_result = evaluate_clinical_rules(features)

    if clinical_result.triggered:
        return {
            "risk_level": clinical_result.forced_risk_level,
            "confidence_score": 1.0,
            "decision_source": "clinical_rules",
            "rule_code": clinical_result.rule_code,
            "explanation": clinical_result.explanation,
            "data_quality_flag": data_quality_flag,
        }

    # Capa 2: Modelo estadístico
    if data_quality_flag == "insufficient_data":
        return {
            "risk_level": None,
            "confidence_score": 0.0,
            "decision_source": "none",
            "explanation": "Datos insuficientes. Se requieren al menos 5 días de registro.",
            "data_quality_flag": data_quality_flag,
        }

    feature_vector = np.array([[features[col] for col in FEATURE_COLUMNS]])
    feature_scaled = _scaler.transform(feature_vector)

    probabilities = _model.predict_proba(feature_scaled)[0]
    predicted_class = int(np.argmax(probabilities))
    confidence = float(np.max(probabilities))

    return {
        "risk_level": RISK_LABELS[predicted_class],
        "confidence_score": round(confidence, 3),
        "probabilities": {
            "Bajo": round(float(probabilities[0]), 3),
            "Medio": round(float(probabilities[1]), 3),
            "Alto": round(float(probabilities[2]), 3),
        },
        "decision_source": "ml_model",
        "data_quality_flag": data_quality_flag,
        "feature_importances": get_top_features(_model, n=3),
    }
```

---

## 5. Endpoints de la API

```
GET  /health                          → Liveness probe
POST /records/{user_id}               → Crear registro diario
GET  /records/{user_id}               → Obtener registros (últimos N días)
GET  /analysis/{user_id}              → Análisis de riesgo actual
GET  /analysis/{user_id}/weekly       → Resumen semanal con tendencias
GET  /recommendations/{user_id}       → Recomendaciones personalizadas
```

**Ejemplo de respuesta `/analysis/{user_id}`:**

```json
{
  "user_id": "u_42",
  "evaluated_at": "2026-05-19T14:30:00Z",
  "risk_level": "Medio",
  "confidence_score": 0.78,
  "decision_source": "ml_model",
  "data_quality_flag": "ok",
  "days_analyzed": 7,
  "probabilities": {
    "Bajo": 0.15,
    "Medio": 0.78,
    "Alto": 0.07
  },
  "top_factors": [
    {"feature": "avg_stress", "importance": 0.31},
    {"feature": "days_sleep_below_5h", "importance": 0.24},
    {"feature": "trend_mood", "importance": 0.18}
  ],
  "disclaimer": "Esta evaluación es orientativa y no constituye diagnóstico clínico."
}
```

---

## 6. Esquema de Base de Datos

```sql
-- Usuarios
CREATE TABLE users (
    id          TEXT PRIMARY KEY,          -- UUID
    age         INTEGER,
    career      TEXT,
    semester    INTEGER,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Registros diarios
CREATE TABLE daily_records (
    id              TEXT PRIMARY KEY,      -- UUID
    user_id         TEXT REFERENCES users(id),
    record_date     DATE NOT NULL,
    mood            INTEGER CHECK (mood BETWEEN 1 AND 5),
    energy          INTEGER CHECK (energy BETWEEN 1 AND 5),
    sleep_hours     REAL CHECK (sleep_hours BETWEEN 0 AND 24),
    stress_level    INTEGER CHECK (stress_level BETWEEN 1 AND 10),
    activities      TEXT,                  -- JSON array: ["study","exercise"]
    is_retroactive  BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, record_date)           -- Un registro por día por usuario
);

-- Evaluaciones de riesgo
CREATE TABLE risk_assessments (
    id                  TEXT PRIMARY KEY,
    user_id             TEXT REFERENCES users(id),
    assessed_at         TIMESTAMP DEFAULT NOW(),
    risk_level          TEXT CHECK (risk_level IN ('Bajo','Medio','Alto')),
    confidence_score    REAL,
    decision_source     TEXT,              -- 'ml_model' | 'clinical_rules'
    rule_code           TEXT,             -- Código de regla clínica si aplica
    data_quality_flag   TEXT,
    days_analyzed       INTEGER,
    raw_features        TEXT,             -- JSON con features de la ventana
    probabilities       TEXT              -- JSON con distribución de probabilidades
);
```

---

## 7. Comandos de Desarrollo (Makefile)

```makefile
# Instalación y configuración
install:
	uv sync

# Generación de datos sintéticos
generate-data:
	python scripts/generate_data.py --samples 1500 --seed 42

# Entrenamiento del modelo
train:
	python scripts/train_model.py --experiment-name sentio_v1

# Evaluación
evaluate:
	python -m model.evaluate --model-path model/artifacts/sentio_model_v1.joblib

# Levantar API en desarrollo
api-dev:
	uvicorn api.main:app --reload --port 8000

# Levantar frontend Streamlit
frontend-dev:
	streamlit run frontend/app.py --server.port 8501

# Levantar todo con Docker
up:
	docker-compose up --build

# Tests
test:
	pytest tests/ -v --asyncio-mode=auto

# Tests con cobertura
test-cov:
	pytest tests/ --cov=api --cov=model --cov-report=html

# Linting
lint:
	ruff check . && black --check .
```

---

## 8. Justificación de Librerías — Monitoreo de Bienestar Emocional

### ¿Por qué Scikit-learn y no PyTorch/TensorFlow?

Los datos de SENTIO son **tabulares y estructurados**: escalas numéricas de 1 a 5, pocas variables (18-20 features), ventanas de 7 días. Los modelos de deep learning son más potentes para datos no estructurados (texto, imágenes, series temporales densas). Para este dominio:

- **Random Forest** supera a las redes neuronales simples en datasets pequeños (<10k filas).
- **Scikit-learn** produce **feature importances** interpretables, esencial para comunicar al usuario qué factores influyeron en su evaluación (explicabilidad clínica).
- El tiempo de entrenamiento es de segundos, no horas, lo que facilita la iteración académica.
- La inferencia es <10ms, muy por debajo del objetivo de 1 segundo.

### ¿Por qué FastAPI y no Flask o Django?

- **FastAPI** tiene validación de entrada nativa con Pydantic v2, lo que garantiza que ningún dato malformado llegue al modelo.
- Documentación OpenAPI automática en `/docs` sin código adicional.
- Soporte async nativo permite manejar múltiples requests concurrentes sin bloquear el event loop.
- Flask sería viable pero requiere más boilerplate para validación y documentación.

### ¿Por qué Streamlit y no React/Vue?

Para un prototipo académico con backend en Python, Streamlit elimina la fricción del desarrollo full-stack. El equipo puede construir visualizaciones de datos complejas (gráficas de tendencia con Plotly) y formularios interactivos en el mismo lenguaje que el modelo. En producción, el frontend podría migrarse a React consumiendo la misma API FastAPI sin cambios en el backend.

### ¿Por qué datos sintéticos?

No existe un dataset público con las variables exactas de SENTIO (registro diario de ánimo + energía + sueño + estrés en formato de 7 días para estudiantes colombianos). Se usa como referencia el dataset [Student Mental Health](https://www.kaggle.com/datasets/shariful07/student-mental-health) de Kaggle para calibrar las distribuciones de las variables. El dataset sintético se genera con `Faker` y `NumPy` controlando las correlaciones entre variables (ej. a mayor estrés, menor calidad de sueño) para producir un dataset estadísticamente coherente con la literatura.

---

## 9. Consideraciones de Seguridad y Privacidad

- **Datos sensibles:** Los registros de bienestar emocional son datos sensibles según la Ley 1581 de 2012 (Colombia). Se requiere consentimiento informado explícito antes de cualquier recolección.
- **Cifrado en reposo:** La base de datos debe estar cifrada (SQLite con SQLCipher en dev, PostgreSQL con TDE en prod).
- **Cifrado en tránsito:** HTTPS obligatorio en cualquier despliegue (Caddy o Nginx como reverse proxy).
- **Sin PII en logs:** Los logs de API no deben contener datos de salud, solo `user_id` y timestamps.
- **Retención de datos:** Política de retención máxima de 1 año de registros históricos con opción de eliminación por parte del usuario.
- **Aviso ético:** Toda evaluación incluye el disclaimer: *"Esta evaluación es orientativa y no constituye un diagnóstico clínico ni reemplaza la valoración de un profesional de salud mental."*

---

## 10. Roadmap de Desarrollo

```
Sprint 1 (Semanas 1-2): Fundación
  ✓ Scaffolding del monorepo
  ✓ Generación de dataset sintético
  ✓ Pipeline de preprocesamiento

Sprint 2 (Semanas 3-4): Modelo
  ○ Entrenamiento y selección de modelo
  ○ Evaluación (objetivo: F1 macro ≥ 0.80, Recall "Alto" ≥ 0.85)
  ○ Motor de reglas clínicas (EC-01 a EC-10)

Sprint 3 (Semanas 5-6): API
  ○ Endpoints CRUD de registros
  ○ Endpoint de análisis con inferencia
  ○ Tests de integración

Sprint 4 (Semanas 7-8): Frontend + Integración
  ○ Interfaz Streamlit completa
  ○ Integración API ↔ Frontend
  ○ Prueba de usuario con dataset real
```

---

*Este documento es la fuente de verdad arquitectural del proyecto. Cualquier cambio estructural debe reflejarse aquí antes de implementarse en el código.*
