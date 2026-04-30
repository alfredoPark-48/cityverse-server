from fastapi import APIRouter, HTTPException
import logging
from src.shared.responses import ApiResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/stats", response_model=ApiResponse)
async def get_stats() -> ApiResponse:
    """Return simulation statistics."""
    from src.infrastructure.api.main import get_simulation
    try:
        sim = get_simulation()
        data = sim.get_stats()
        return ApiResponse.ok(data=data)
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return ApiResponse.error(
            message="Failed to retrieve simulation statistics",
            code="STATS_FETCH_FAILED"
        )
