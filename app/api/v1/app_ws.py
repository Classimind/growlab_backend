from fastapi import APIRouter,WebSocket
from app.services.actuator_status_service import ActuatorStatusService
from app.services.ws_connection_manager_sensor import sensormanager
from app.services.sensor_service import CollectSensorValueService
from app.services.ws_connection_manager import manager
router = APIRouter()


#-------------------------------------------------------------
# ws for the realtime montitoring of the state of the actuators
#--------------------------------------------------------------
@router.websocket("/actuators/{actuatorId}")
async def websocket_endpoint(websocket:WebSocket,actuatorId:str):
    await manager.connect(actuatorId,websocket)
    service = ActuatorStatusService()
    try:
        last_status = await service.get_actuator_status_by_actuator_id(actuatorId)
        if last_status:
            await websocket.send_json({"type":"init","status":last_status['value']})
        else:
            await websocket.send_json({"type":"init","status":'none'})
        
        # keep connection alive 
        while True:
            await websocket.receive_text()

    except Exception as e:
        print(f"Error: {e}")
    finally:
        manager.disconnect(actuatorId,websocket)

@router.websocket("/sensors/live/{sensor_id}")
async def websocket_sensor(websocket: WebSocket, sensor_id: str):
    await sensormanager.connect(sensor_id, websocket)
    try:
        while True:
            await websocket.receive_text() 
    except Exception as e:
        print(f"Error in websocket: {e}")
    finally:
        manager.disconnect(sensor_id, websocket)


