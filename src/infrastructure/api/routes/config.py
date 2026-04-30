from fastapi import APIRouter, HTTPException
import logging
from src.shared.responses import ApiResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/config", response_model=ApiResponse)
async def get_config() -> ApiResponse:
    """Return simulation configuration."""
    from src.infrastructure.api.main import get_simulation
    try:
        sim = get_simulation()
        data = sim.get_config()
        return ApiResponse.ok(data=data)
    except Exception as e:
        logger.error(f"Error fetching config: {e}")
        return ApiResponse.error(
            message="Failed to retrieve simulation config",
            code="CONFIG:FETCH:ERROR"
        )


@router.post("/config", response_model=ApiResponse)
async def update_config(config: dict) -> ApiResponse:
    """Update simulation configuration."""
    from src.infrastructure.api.main import get_simulation
    try:
        sim = get_simulation()
        sim.set_config(config)
        return ApiResponse.ok(
            data=sim.get_config(),
            message="Configuration updated successfully",
            code="CONFIG:UPDATE:SUCCESS"
        )
    except ValueError as e:
        return ApiResponse.error(message=str(e), code="CONFIG:VALIDATION:ERROR")
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return ApiResponse.error(
            message="Failed to update simulation config",
            code="CONFIG:UPDATE:ERROR"
        )
