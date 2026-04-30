from fastapi import APIRouter, HTTPException
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/stats")
async def get_stats() -> dict:
    """Return simulation statistics."""
    from src.infrastructure.api.main import get_simulation
    try:
        sim = get_simulation()
        return sim.get_stats()
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve simulation statistics")
