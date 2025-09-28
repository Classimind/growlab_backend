from fastapi import APIRouter,WebSocket
from app.services.actuator_status_service import ActuatorStatusService
from app.services.ws_connection_manager import manager
router = APIRouter()

#-------------------------------------------------------------
# ws for the realtime montitoring of the state of the actuators
#--------------------------------------------------------------
@router.websocket("/actuators/{farm_name}/{actuator_name}")
async def websocket_endpoint(websocket:WebSocket,farm_name:str,actuator_name:str):
    await manager.connect(farm_name,actuator_name,websocket)
    service = ActuatorStatusService()
    try:
        last_status = await service.get_last_status(actuator_name,farm_name)
        if last_status:
            await websocket.send_json({"type":"init","status":last_status.status.value})
        
        # keep connection alive 
        while True:
            await websocket.receive_text()

    except Exception as e:
        print(f"Error: {e}")
    finally:
        manager.disconnect(farm_name,actuator_name,websocket)


