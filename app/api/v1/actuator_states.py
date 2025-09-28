from fastapi import APIRouter
from app.services.actuator_status_service import ActuatorStatusService
router = APIRouter()


#--------------------------------------
# GET the status of the actuator by name
#--------------------------------------
@router.get("/{farm_name}/{actuator_name}/last-status")
async def get_last_status(farm_name:str,actuator_name:str):
    service = ActuatorStatusService()
    return await service.get_last_status(actuator_name,farm_name)
