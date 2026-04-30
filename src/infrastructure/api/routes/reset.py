from fastapi import APIRouter, HTTPException
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/reset")
async def reset_simulation() -> dict:
    """Reinitialize the simulation to its initial state."""
    from src.infrastructure.api.main import get_simulation
    try:
        sim = get_simulation()
        return sim.reset()
    except Exception as e:
        logger.error(f"Error resetting simulation: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset simulation")
