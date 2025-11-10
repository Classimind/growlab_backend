from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from app.models.actuator import Actuator, ResponseActuator, ActuatorStatus
from app.services.actuator import ActuatorService  




router = APIRouter(prefix="/actuators", tags=["Sensors"])

actuator_service = ActuatorService()

# Endpoint for creating an actuator
@router.post("/", response_model=ResponseActuator, status_code=status.HTTP_201_CREATED)
async def create_actuator(actuator: Actuator):
    try:
        success,id = await actuator_service.create_actuator(actuator)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create actuator."
            )
        # Return the created actuator (include the ID in the response)
        actuator_data = await actuator_service.get_actuator_by_id(id)
        
        return actuator_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Endpoint to get an actuator by ID
@router.get("/{actuator_id}", response_model=ResponseActuator)
async def get_actuator_by_id(actuator_id: str):
    actuator = await actuator_service.get_actuator_by_id(actuator_id)
    if actuator is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Actuator with ID {actuator_id} not found."
        )
    return actuator


# Endpoint to get all actuators (filter by farmId if provided)
@router.get("/", response_model=List[ResponseActuator])
async def get_all_actuators(farm_id: Optional[str] = None):
    actuators = await actuator_service.get_all_actuators(farm_id)
    return actuators


# Endpoint to update an actuator by ID
@router.put("/{actuator_id}", response_model=ResponseActuator)
async def update_actuator(actuator_id: str, actuator_update: Actuator):
    updated_actuator = await actuator_service.update_actuator(actuator_id, actuator_update)
    if updated_actuator is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Actuator with ID {actuator_id} not found."
        )
    return updated_actuator


# Endpoint to delete an actuator by ID
@router.delete("/{actuator_id}", response_model=dict)
async def delete_actuator(actuator_id: str):
    success = await actuator_service.delete_actuator(actuator_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Actuator with ID {actuator_id} not found."
        )
    return {"detail": f"Actuator with ID {actuator_id} deleted successfully."}


# Endpoint to create a new actuator status
@router.post("/actuator-status/", response_model=ActuatorStatus, status_code=status.HTTP_201_CREATED)
async def create_actuator_status(actuator_status: ActuatorStatus):
    try:
        new_status = await actuator_service.create_actuator_status(actuator_status)
        return new_status
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Endpoint to get an actuator status by actuator ID
@router.get("/actuator-status/{actuator_id}", response_model=ActuatorStatus)
async def get_actuator_status_by_actuator_id(actuator_id: str):
    status = await actuator_service.get_actuator_status_by_actuator_id(actuator_id)
    if status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Actuator status for actuator with ID {actuator_id} not found."
        )
    return status


# Endpoint to update actuator status
@router.put("/actuator-status/{actuator_id}", response_model=ActuatorStatus)
async def update_actuator_status(actuator_id: str, value: str):
    updated_status = await actuator_service.update_actuator_status(actuator_id, value)
    if updated_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Actuator status for actuator with ID {actuator_id} not found."
        )
    return updated_status
