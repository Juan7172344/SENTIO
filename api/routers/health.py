"""Health / liveness (placeholder)."""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
def liveness() -> dict[str, str]:
    return {"status": "ok"}
