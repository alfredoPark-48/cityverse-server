from fastapi import APIRouter, HTTPException
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/step")
async def step_simulation() -> dict:
    """Advance the simulation by one tick and return updated state."""
    from src.infrastructure.api.main import get_simulation
    try:
        sim = get_simulation()
        return sim.step()
    except Exception as e:
        logger.error(f"Error stepping simulation: {e}")
        raise HTTPException(status_code=500, detail="Failed to advance simulation step")
