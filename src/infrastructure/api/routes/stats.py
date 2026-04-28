"""GET /stats – simulation statistics."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/stats")
async def get_stats() -> dict:
    """Return simulation statistics."""
    from src.infrastructure.api.main import get_simulation

    sim = get_simulation()
    return sim.get_stats()
