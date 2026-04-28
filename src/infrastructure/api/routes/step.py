"""GET /step – advance simulation by one tick."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/step")
async def step_simulation() -> dict:
    """Advance the simulation by one tick and return updated state."""
    from src.infrastructure.api.main import get_simulation

    sim = get_simulation()
    return sim.step()
