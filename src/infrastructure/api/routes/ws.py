from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import logging
import json
from src.shared.responses import ApiResponse

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
                    # Advance simulation
                    sim.step()
                    # After initial sync, we don't need to send the grid every time
                    frame = sim._model.get_state_snapshot(include_grid=False)
                    await websocket.send_json(frame)
                    
                    if not frame["running"]:
                        playing = False
                        await websocket.send_json(ApiResponse.ok(
                            message="Simulation completed",
                            code="SIMULATION:RUN:COMPLETED"
                        ).model_dump())
                
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
                await websocket.send_json(ApiResponse.ok(
                    message="Simulation started",
                    code="SIMULATION:PLAY:SUCCESS"
                ).model_dump())
            elif cmd_type == "pause":
                playing = False
                logger.info("Simulation paused via WS")
                await websocket.send_json(ApiResponse.ok(
                    message="Simulation paused",
                    code="SIMULATION:PAUSE:SUCCESS"
                ).model_dump())
            elif cmd_type == "step":
                playing = False
                sim.step()
                await websocket.send_json(sim._model.get_state_snapshot(include_grid=False))
                await websocket.send_json(ApiResponse.ok(
                    message="Step executed",
                    code="SIMULATION:STEP:SUCCESS"
                ).model_dump())
            elif cmd_type == "reset":
                playing = False
                state = sim.reset()
                # On reset, send full state including grid
                await websocket.send_json(state)
                await websocket.send_json(ApiResponse.ok(
                    message="Simulation reset to initial state",
                    code="SIMULATION:RESET:SUCCESS"
                ).model_dump())
            elif cmd_type == "set_speed":
                speed_ms = command.get("value", 300)
                tick_delay = speed_ms / 1000.0
                await websocket.send_json(ApiResponse.ok(
                    message=f"Speed set to {speed_ms}ms per tick",
                    code="SIMULATION:SPEED:UPDATED",
                    data={"speed": speed_ms}
                ).model_dump())
            elif cmd_type == "update_config":
                try:
                    sim.set_config(command.get("config", {}))
                    await websocket.send_json({
                        "type": "config_updated", 
                        "config": sim.get_config()
                    })
                    await websocket.send_json(ApiResponse.ok(
                        message="Configuration updated and applied",
                        code="CONFIG:UPDATE:SUCCESS"
                    ).model_dump())
                except Exception as e:
                    await websocket.send_json(ApiResponse.error(
                        message=f"Failed to update config: {str(e)}",
                        code="CONFIG:UPDATE:ERROR"
                    ).model_dump())
                
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
