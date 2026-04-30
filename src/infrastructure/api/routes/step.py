from fastapi import APIRouter, HTTPException
import logging
from src.shared.responses import ApiResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/step", response_model=ApiResponse)
async def step_simulation() -> ApiResponse:
    """Advance the simulation by one tick and return updated state."""
    from src.infrastructure.api.main import get_simulation
    try:
        sim = get_simulation()
        data = sim.step()
        return ApiResponse.ok(
            data=data,
            message="Simulation stepped successfully",
            code="SIMULATION:STEP:SUCCESS"
        )
    except Exception as e:
        logger.error(f"Error stepping simulation: {e}")
        return ApiResponse.error(
            message="Failed to advance simulation step",
            code="SIMULATION:STEP:ERROR"
        )
