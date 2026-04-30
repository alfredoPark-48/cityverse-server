from fastapi import APIRouter, HTTPException
import logging
from src.shared.responses import ApiResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/reset", response_model=ApiResponse)
async def reset_simulation() -> ApiResponse:
    """Reinitialize the simulation to its initial state."""
    from src.infrastructure.api.main import get_simulation
    try:
        sim = get_simulation()
        data = sim.reset()
        return ApiResponse.ok(
            data=data, 
            message="Simulation reset successfully", 
            code="SIM_RESET_SUCCESS"
        )
    except Exception as e:
        logger.error(f"Error resetting simulation: {e}")
        return ApiResponse.error(
            message=f"Failed to reset simulation: {str(e)}",
            code="SIM_RESET_FAILED"
        )
