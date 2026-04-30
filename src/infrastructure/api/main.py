"""FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.application.services.simulation_service import SimulationService
from src.infrastructure.api.routes import step, state, reset, stats, config, ws

app = FastAPI(
    title="Cityverse Backend",
    description="City traffic simulation powered by Mesa and FastAPI",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton simulation service
_simulation: SimulationService | None = None


def get_simulation() -> SimulationService:
    """Get or create the simulation service singleton."""
    global _simulation
    if _simulation is None:
        _simulation = SimulationService()
    return _simulation


# Register API routes
app.include_router(step.router)
app.include_router(state.router)
app.include_router(reset.router)
app.include_router(stats.router)
app.include_router(config.router)
app.include_router(ws.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "alive"}
