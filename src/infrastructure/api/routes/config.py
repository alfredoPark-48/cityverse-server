"""GET /config – simulation configuration."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/config")
async def get_config() -> dict:
    """Return simulation configuration."""
    from src.infrastructure.api.main import get_simulation

    sim = get_simulation()
    return sim.get_config()
