"""Esquema Pydantic del registro diario (evolución hacia fuente de verdad compartida)."""

from datetime import date
from typing import Any

from pydantic import BaseModel, Field, field_validator


class DailyRecordSchema(BaseModel):
    """Registro diario alineado con la tabla `daily_records` del documento de arquitectura."""

    record_date: date
    mood: int = Field(ge=1, le=5)
    energy: int = Field(ge=1, le=5)
    sleep_hours: float = Field(ge=0, le=24)
    stress_level: int = Field(ge=1, le=10)
    activities: list[str] = Field(default_factory=list)
    is_retroactive: bool = False

    @field_validator("activities", mode="before")
    @classmethod
    def coerce_activities(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return list(v)
