"""GET /state – return full simulation state."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/state")
async def get_state() -> dict:
    """Return current simulation state without advancing."""
    from src.infrastructure.api.main import get_simulation

    sim = get_simulation()
    return sim.get_state()
