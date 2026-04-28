"""POST /reset – reinitialize the simulation."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/reset")
async def reset_simulation() -> dict:
    """Reinitialize the simulation to its initial state."""
    from src.infrastructure.api.main import get_simulation

    sim = get_simulation()
    return sim.reset()
