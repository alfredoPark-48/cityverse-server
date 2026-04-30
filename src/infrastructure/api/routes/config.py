from fastapi import APIRouter, HTTPException
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/config")
async def get_config() -> dict:
    """Return simulation configuration."""
    from src.infrastructure.api.main import get_simulation
    try:
        sim = get_simulation()
        return sim.get_config()
    except Exception as e:
        logger.error(f"Error fetching config: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve simulation config")


@router.post("/config")
async def update_config(config: dict) -> dict:
    """Update simulation configuration."""
    from src.infrastructure.api.main import get_simulation
    try:
        sim = get_simulation()
        # Debugging the AttributeError
        print(f"DEBUG: sim object type: {type(sim)}")
        print(f"DEBUG: has set_config: {hasattr(sim, 'set_config')}")
        
        sim.set_config(config)
        return {"status": "success", "config": sim.get_config()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update simulation config")
