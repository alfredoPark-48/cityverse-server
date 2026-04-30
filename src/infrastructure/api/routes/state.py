"""GET /state – return full simulation state."""

from fastapi import APIRouter
from src.shared.responses import ApiResponse

router = APIRouter()


@router.get("/state", response_model=ApiResponse)
async def get_state() -> ApiResponse:
    """Return current simulation state without advancing."""
    from src.infrastructure.api.main import get_simulation

    sim = get_simulation()
    data = sim.get_state()
    return ApiResponse.ok(data=data, code="STATE:FETCH:SUCCESS")
