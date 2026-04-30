from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    from src.infrastructure.api.main import get_simulation
    
    await websocket.accept()
    sim = get_simulation()
    
    # Send initial state with grid
    initial_state = sim.get_state()
    await websocket.send_json(initial_state)
    
    playing = False
    tick_delay = 0.3 # Default 300ms
    
    async def simulation_loop():
        nonlocal playing
        try:
            while True:
                if playing:
                    state = sim.step()
                    # After initial sync, we don't need to send the grid every time
                    # unless explicitly requested or during a reset.
                    # For simplicity in this refactor, we exclude grid from stream frames.
                    frame = sim._model.get_state_snapshot(include_grid=False)
                    await websocket.send_json(frame)
                    
                    if not frame["running"]:
                        playing = False
                
                await asyncio.sleep(tick_delay)
        except Exception as e:
            logger.error(f"Error in simulation loop: {e}")

    # Start simulation loop in the background
    loop_task = asyncio.create_task(simulation_loop())

    try:
        while True:
            # Wait for commands from the client
            data = await websocket.receive_text()
            command = json.loads(data)
            
            cmd_type = command.get("type")
            
            if cmd_type == "play":
                playing = True
                logger.info("Simulation started via WS")
            elif cmd_type == "pause":
                playing = False
                logger.info("Simulation paused via WS")
            elif cmd_type == "step":
                playing = False
                state = sim.step()
                await websocket.send_json(sim._model.get_state_snapshot(include_grid=False))
            elif cmd_type == "reset":
                playing = False
                state = sim.reset()
                # On reset, send full state including grid
                await websocket.send_json(state)
            elif cmd_type == "set_speed":
                tick_delay = command.get("value", 300) / 1000.0
            elif cmd_type == "update_config":
                sim.set_config(command.get("config", {}))
                # Optionally send back new config to confirm
                await websocket.send_json({"type": "config_updated", "config": sim.get_config()})
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        loop_task.cancel()
        try:
            await loop_task
        except asyncio.CancelledError:
            pass
