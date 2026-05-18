"""Persistencia SQLite del perfil estudiantil (US-01)."""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from dataclasses import dataclass
from datetime import datetime, timezone, date
from typing import Optional, List
import json
from uuid import uuid4

from src.config import database_path


@dataclass(frozen=True)
class StudentProfile:
    id: str
    session_key: str
    age: int
    career: str
    semester: int
    habitual_sleep_hours: float
    physical_activity_days_per_week: int
    base_academic_stress: int


@dataclass(frozen=True)
class DailyRecord:
    id: str
    user_id: str
    record_date: str
    mood: int
    energy: int
    sleep_hours: float
    stress_level: int
    activities: List[str]
    is_retroactive: bool
    created_at: str


@dataclass(frozen=True)
class RiskAssessment:
    id: str
    user_id: str
    assessed_at: str
    risk_level: str
    confidence_score: float
    decision_source: str
    rule_code: Optional[str]
    data_quality_flag: str
    days_analyzed: int
    raw_features: dict
    probabilities: dict


def connect() -> sqlite3.Connection:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def init_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS student_profiles (
            id TEXT PRIMARY KEY,
            session_key TEXT NOT NULL UNIQUE,
            age INTEGER NOT NULL,
            career TEXT NOT NULL,
            semester INTEGER NOT NULL,
            habitual_sleep_hours REAL NOT NULL,
            physical_activity_days_per_week INTEGER NOT NULL,
            base_academic_stress INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_records (
            id TEXT PRIMARY KEY,
            user_id TEXT REFERENCES student_profiles(id),
            record_date TEXT NOT NULL,
            mood INTEGER CHECK (mood BETWEEN 1 AND 5),
            energy INTEGER CHECK (energy BETWEEN 1 AND 5),
            sleep_hours REAL CHECK (sleep_hours BETWEEN 0 AND 24),
            stress_level INTEGER CHECK (stress_level BETWEEN 1 AND 10),
            activities TEXT,
            is_retroactive BOOLEAN DEFAULT FALSE,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, record_date)
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS risk_assessments (
            id TEXT PRIMARY KEY,
            user_id TEXT REFERENCES student_profiles(id),
            assessed_at TEXT NOT NULL,
            risk_level TEXT CHECK (risk_level IN ('Bajo','Medio','Alto')),
            confidence_score REAL,
            decision_source TEXT,
            rule_code TEXT,
            data_quality_flag TEXT,
            days_analyzed INTEGER,
            raw_features TEXT,
            probabilities TEXT
        );
        """
    )
    conn.commit()


def get_profile_by_id(conn: sqlite3.Connection, profile_id: str) -> Optional[StudentProfile]:
    row = conn.execute(
        "SELECT * FROM student_profiles WHERE id = ? LIMIT 1",
        (profile_id,),
    ).fetchone()
    if row is None:
        return None
    return StudentProfile(
        id=row["id"],
        session_key=row["session_key"],
        age=int(row["age"]),
        career=str(row["career"]),
        semester=int(row["semester"]),
        habitual_sleep_hours=float(row["habitual_sleep_hours"]),
        physical_activity_days_per_week=int(row["physical_activity_days_per_week"]),
        base_academic_stress=int(row["base_academic_stress"]),
    )


def profile_as_model_inputs(profile: StudentProfile) -> dict[str, float]:
    """Vector de entrada alineado con `model.preprocessing.FEATURE_COLUMNS`."""
    return {
        "age": float(profile.age),
        "semester": float(profile.semester),
        "habitual_sleep_hours": float(profile.habitual_sleep_hours),
        "base_academic_stress": float(profile.base_academic_stress),
        "physical_activity_days_per_week": float(profile.physical_activity_days_per_week),
    }


def get_profile_by_session(conn: sqlite3.Connection, session_key: str) -> Optional[StudentProfile]:
    row = conn.execute(
        "SELECT * FROM student_profiles WHERE session_key = ? LIMIT 1",
        (session_key,),
    ).fetchone()
    if row is None:
        return None
    return StudentProfile(
        id=row["id"],
        session_key=row["session_key"],
        age=int(row["age"]),
        career=str(row["career"]),
        semester=int(row["semester"]),
        habitual_sleep_hours=float(row["habitual_sleep_hours"]),
        physical_activity_days_per_week=int(row["physical_activity_days_per_week"]),
        base_academic_stress=int(row["base_academic_stress"]),
    )


def delete_profile_by_session(conn: sqlite3.Connection, session_key: str) -> int:
    """Elimina el perfil ligado a la sesión. Devuelve filas borradas."""
    cur = conn.execute(
        "DELETE FROM student_profiles WHERE session_key = ?",
        (session_key,),
    )
    conn.commit()
    return int(cur.rowcount)


def insert_profile(
    conn: sqlite3.Connection,
    *,
    session_key: str,
    age: int,
    career: str,
    semester: int,
    habitual_sleep_hours: float,
    physical_activity_days_per_week: int,
    base_academic_stress: int,
) -> StudentProfile:
    profile_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO student_profiles (
            id, session_key, age, career, semester,
            habitual_sleep_hours, physical_activity_days_per_week,
            base_academic_stress, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            profile_id,
            session_key,
            age,
            career.strip(),
            semester,
            habitual_sleep_hours,
            physical_activity_days_per_week,
            base_academic_stress,
            created_at,
        ),
    )
    conn.commit()
    profile = get_profile_by_session(conn, session_key)
    if profile is None:
        raise RuntimeError("No se pudo recuperar el perfil recién creado.")
    return profile


def insert_daily_record(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    record_date: str,
    mood: int,
    energy: int,
    sleep_hours: float,
    stress_level: int,
    activities: List[str],
    is_retroactive: bool = False,
) -> DailyRecord:
    record_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    activities_json = json.dumps(activities)
    
    conn.execute(
        """
        INSERT INTO daily_records (
            id, user_id, record_date, mood, energy, sleep_hours,
            stress_level, activities, is_retroactive, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, record_date) DO UPDATE SET
            mood=excluded.mood,
            energy=excluded.energy,
            sleep_hours=excluded.sleep_hours,
            stress_level=excluded.stress_level,
            activities=excluded.activities,
            is_retroactive=excluded.is_retroactive;
        """,
        (
            record_id, user_id, record_date, mood, energy, sleep_hours,
            stress_level, activities_json, is_retroactive, created_at
        )
    )
    conn.commit()
    
    return DailyRecord(
        id=record_id,
        user_id=user_id,
        record_date=record_date,
        mood=mood,
        energy=energy,
        sleep_hours=sleep_hours,
        stress_level=stress_level,
        activities=activities,
        is_retroactive=is_retroactive,
        created_at=created_at
    )


def get_daily_records_by_user(conn: sqlite3.Connection, user_id: str, limit: int = 7) -> List[DailyRecord]:
    rows = conn.execute(
        "SELECT * FROM daily_records WHERE user_id = ? ORDER BY record_date DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    
    records = []
    for row in rows:
        records.append(DailyRecord(
            id=row["id"],
            user_id=row["user_id"],
            record_date=row["record_date"],
            mood=int(row["mood"]),
            energy=int(row["energy"]),
            sleep_hours=float(row["sleep_hours"]),
            stress_level=int(row["stress_level"]),
            activities=json.loads(row["activities"]) if row["activities"] else [],
            is_retroactive=bool(row["is_retroactive"]),
            created_at=row["created_at"],
        ))
    return records


def insert_risk_assessment(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    risk_level: str,
    confidence_score: float,
    decision_source: str,
    rule_code: Optional[str],
    data_quality_flag: str,
    days_analyzed: int,
    raw_features: dict,
    probabilities: dict,
) -> RiskAssessment:
    assessment_id = str(uuid4())
    assessed_at = datetime.now(timezone.utc).isoformat()
    
    conn.execute(
        """
        INSERT INTO risk_assessments (
            id, user_id, assessed_at, risk_level, confidence_score,
            decision_source, rule_code, data_quality_flag, days_analyzed,
            raw_features, probabilities
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            assessment_id, user_id, assessed_at, risk_level, confidence_score,
            decision_source, rule_code, data_quality_flag, days_analyzed,
            json.dumps(raw_features), json.dumps(probabilities)
        )
    )
    conn.commit()
    
    return RiskAssessment(
        id=assessment_id,
        user_id=user_id,
        assessed_at=assessed_at,
        risk_level=risk_level,
        confidence_score=confidence_score,
        decision_source=decision_source,
        rule_code=rule_code,
        data_quality_flag=data_quality_flag,
        days_analyzed=days_analyzed,
        raw_features=raw_features,
        probabilities=probabilities
    )


def get_latest_risk_assessment(conn: sqlite3.Connection, user_id: str) -> Optional[RiskAssessment]:
    row = conn.execute(
        "SELECT * FROM risk_assessments WHERE user_id = ? ORDER BY assessed_at DESC LIMIT 1",
        (user_id,)
    ).fetchone()
    if row is None:
        return None
    return RiskAssessment(
        id=row["id"],
        user_id=row["user_id"],
        assessed_at=row["assessed_at"],
        risk_level=row["risk_level"],
        confidence_score=float(row["confidence_score"]),
        decision_source=row["decision_source"],
        rule_code=row["rule_code"],
        data_quality_flag=row["data_quality_flag"],
        days_analyzed=int(row["days_analyzed"]),
        raw_features=json.loads(row["raw_features"]) if row["raw_features"] else {},
        probabilities=json.loads(row["probabilities"]) if row["probabilities"] else {}
    )
