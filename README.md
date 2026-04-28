# Cityverse Backend

City traffic simulation backend powered by **Mesa**, **FastAPI**, and **Docker**.

## Architecture

```
src/
├── domain/           # Entities, value objects, interfaces (pure logic)
│   ├── entities/     # Agent, CarAgent, PedestrianAgent, TrafficLight, Building
│   ├── value_objects/ # Position, Direction, GridCell
│   └── interfaces/   # IMovable, ICollidable
├── application/      # Use cases and DTOs
│   ├── services/     # SimulationService, PathfindingService, TrafficLightService
│   └── dtos/         # AgentStateDTO
├── infrastructure/   # External concerns
│   ├── api/          # FastAPI app and routes
│   ├── persistence/  # Grid file loader
│   └── models/       # Mesa CityModel
└── shared/           # Config, constants
```

## Quick Start

### Local

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.infrastructure.api.main:app --reload
```

### Docker

```bash
docker compose up --build
```

### Verify

```bash
curl http://localhost:8000/health
# → {"status": "alive"}
```

## API Endpoints

| Method | Path      | Description                          |
|--------|-----------|--------------------------------------|
| GET    | `/health` | Health check                         |
| GET    | `/step`   | Advance simulation 1 tick            |
| GET    | `/state`  | Full snapshot (grid, agents, lights)  |
| POST   | `/reset`  | Reinitialize simulation              |
| GET    | `/stats`  | Active counts, avg wait times        |
| GET    | `/config` | Grid dimensions, spawn points        |

## Grid Format

The city is defined in `data/city_grid.txt` (30×30):

| Char   | Meaning                |
|--------|------------------------|
| `v^><` | Directional roads      |
| `s`    | Sidewalk               |
| `c`    | Crosswalk              |
| `B`    | Building               |
| `DURL` | Traffic lights (dir)   |
| `O`    | Roundabout             |
| `P`    | Parking                |
| `.`    | Grass                  |

## Tech Stack

- **Python 3.11+**
- **FastAPI** — REST API
- **Mesa** — Agent-based simulation
- **Pydantic** — Data validation
- **Docker** — Containerization
- **Railway** — Deployment

## Tests

```bash
pytest tests/ -v
```
