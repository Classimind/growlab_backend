from fastapi import APIRouter, HTTPException, status,Query,Depends
from typing import List, Optional
from app.models.actuator import Actuator, ResponseActuator, ActuatorStatus
from app.services.actuator import ActuatorService  
from app.services.actuator_status_service import ActuatorStatusService
from app.services.mqtt_service import mqtt_service
from app.services.ws_connection_manager import manager
from app.core.dependencies import get_current_user,can_access_farm
from bson import ObjectId
from app.api.v1.farm import get_lab_service


router = APIRouter(prefix="/actuators", tags=["Sensors"])

actuator_service = ActuatorService()
actuator_status_service = ActuatorStatusService()


# Endpoint for creating an actuator
# @router.post("/", response_model=ResponseActuator, status_code=status.HTTP_201_CREATED)
# async def create_actuator(actuator: Actuator):
#     try:
#         success,id = await actuator_service.create_actuator(actuator)
#         if not success:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Failed to create actuator."
#             )
#         # Return the created actuator (include the ID in the response)
#         actuator_data = await actuator_service.get_actuator_by_id(id)
        
#         return actuator_data
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=str(e)
#         )
@router.post("/", response_model=ResponseActuator, status_code=status.HTTP_201_CREATED)
async def create_actuator(
    actuator: Actuator,
    user = Depends(get_current_user),
    lab_service = DeprecationWarning(get_lab_service)
):
    try:
        user_id = str(user["user_id"])

        lab = await lab_service.get_lab_by_id(actuator.lab_id)

        if not lab:
            raise HTTPException(
                status_code=404,
                detail="Lab not found"
            )

        if not can_access_farm(user_id, lab.farm_id,'create'):
            raise HTTPException(
                status_code=403,
                detail="You are not allowed to access this lab"
            )

        success, id = await actuator_service.create_actuator(actuator)

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to create actuator."
            )

        return await actuator_service.get_actuator_by_id(id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# Endpoint to get an actuator by ID
# @router.get("/{actuator_id}", response_model=ResponseActuator)
# async def get_actuator_by_id(actuator_id: str):
#     actuator = await actuator_service.get_actuator_by_id(actuator_id)
#     if actuator is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Actuator with ID {actuator_id} not found."
#         )
#     return actuator

@router.get("/{actuator_id}", response_model=ResponseActuator)
async def get_actuator_by_id(
    actuator_id: str,
    user = Depends(get_current_user),
    lab_service = Depends(get_lab_service)
):
    try:
        user_id = str(user["user_id"])

        actuator = await actuator_service.get_actuator_by_id(actuator_id)

        if actuator is None:
            raise HTTPException(
                status_code=404,
                detail=f"Actuator with ID {actuator_id} not found."
            )

        lab = await lab_service.get_lab_by_id(actuator["farmId"])

        if not lab:
            raise HTTPException(
                status_code=404,
                detail="Lab not found for this actuator"
            )

        allowed = await can_access_farm(user_id, lab)

        if not allowed:
            raise HTTPException(
                status_code=403,
                detail="You are not allowed to access this actuator"
            )

        return actuator

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# Endpoint to get all actuators (filter by farmId if provided)
# @router.get("/", response_model=List[ResponseActuator])
# async def get_all_actuators(farm_id: Optional[str] = None):
#     actuators = await actuator_service.get_all_actuators(farm_id)
#     return actuators

@router.get("/", response_model=List[ResponseActuator])
async def get_all_actuators(
    farm_id: Optional[str] = None,
    user = Depends(get_current_user)
):
    try:
        user_id = str(user["user_id"])
        query_farm_id = farm_id
        if farm_id:
            allowed = await can_access_farm(user_id, farm_id)

            if not allowed:
                raise HTTPException(
                    status_code=403,
                    detail="You are not allowed to access this farm"
                )
        actuators = await actuator_service.get_all_actuators(query_farm_id)

        return actuators

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# Endpoint to update an actuator by ID
# @router.put("/{actuator_id}", response_model=ResponseActuator)
# async def update_actuator(actuator_id: str, actuator_update: Actuator):
#     updated_actuator = await actuator_service.update_actuator(actuator_id, actuator_update)
#     if updated_actuator is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Actuator with ID {actuator_id} not found."
#         )
#     return updated_actuator


@router.put("/{actuator_id}", response_model=ResponseActuator)
async def update_actuator(
    actuator_id: str,
    actuator_update: Actuator,
    user = Depends(get_current_user),
    lab_service = Depends(get_lab_service)
):
    try:
        user_id = str(user["user_id"])

        existing_actuator = await actuator_service.get_actuator_by_id(actuator_id)

        if not existing_actuator:
            raise HTTPException(
                status_code=404,
                detail=f"Actuator with ID {actuator_id} not found."
            )

        lab = await lab_service.get_lab_by_id(existing_actuator["farmId"])

        if not lab:
            raise HTTPException(
                status_code=404,
                detail="Lab not found for this actuator"
            )

        allowed = await can_access_farm(user_id, lab,'update')

        if not allowed:
            raise HTTPException(
                status_code=403,
                detail="You are not allowed to update this actuator"
            )

        updated_actuator = await actuator_service.update_actuator(
            actuator_id,
            actuator_update
        )

        return updated_actuator

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# Endpoint to delete an actuator by ID
# @router.delete("/{actuator_id}", response_model=dict)
# async def delete_actuator(actuator_id: str):
#     success = await actuator_service.delete_actuator(actuator_id)
#     if not success:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Actuator with ID {actuator_id} not found."
#         )
#     return {"detail": f"Actuator with ID {actuator_id} deleted successfully."}

@router.delete("/{actuator_id}", response_model=dict)
async def delete_actuator(
    actuator_id: str,
    user = Depends(get_current_user),
    lab_service = Depends(get_lab_service)
):
    try:
        user_id = str(user["user_id"])

        actuator = await actuator_service.get_actuator_by_id(actuator_id)

        if not actuator:
            raise HTTPException(
                status_code=404,
                detail=f"Actuator with ID {actuator_id} not found."
            )

        lab = await lab_service.get_lab_by_id(actuator["farmId"])

        if not lab:
            raise HTTPException(
                status_code=404,
                detail="Lab not found for this actuator"
            )

        allowed = await can_access_farm(user_id, lab,'delete')

        if not allowed:
            raise HTTPException(
                status_code=403,
                detail="You are not allowed to delete this actuator"
            )

        success = await actuator_service.delete_actuator(actuator_id)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete actuator"
            )

        return {
            "detail": f"Actuator with ID {actuator_id} deleted successfully."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# Endpoint to create a new actuator status
# @router.post("/actuator-command/",  status_code=status.HTTP_201_CREATED)
# async def send_actuator_command(actuator_status: ActuatorStatus):
#     try:
#         publish_result = mqtt_service.publish(actuator_status.actuator_id,actuator_status.value,qos=0)
#         if publish_result:
#             #update the websocket 
#             await manager.send_update(actuatorId=actuator_status.actuator_id,value=actuator_status.value)
#             await actuator_status_service.create_actuator_status(actuator_status)
#             return {'status':'ok'}
#         return {'status':'failed'}
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=str(e)
#         )

@router.post("/actuator-command/", status_code=status.HTTP_201_CREATED)
async def send_actuator_command(
    actuator_status: ActuatorStatus,
    user = Depends(get_current_user),
    lab_service = Depends(get_lab_service)
):
    try:
        user_id = str(user["user_id"])

        actuator = await actuator_service.get_actuator_by_id(
            actuator_status.actuator_id
        )

        if not actuator:
            raise HTTPException(
                status_code=404,
                detail="Actuator not found"
            )

        lab = await lab_service.get_lab_by_id(actuator["farmId"])

        if not lab:
            raise HTTPException(
                status_code=404,
                detail="Lab not found"
            )

        allowed = await can_access_farm(user_id, lab,'create')

        if not allowed:
            raise HTTPException(
                status_code=403,
                detail="You are not allowed to control this actuator"
            )

        publish_result = mqtt_service.publish(
            actuator_status.actuator_id,
            actuator_status.value,
            qos=0
        )

        if not publish_result:
            return {"status": "failed"}

        await actuator_status_service.create_actuator_status(actuator_status)

        await manager.send_update(
            actuatorId=actuator_status.actuator_id,
            value=actuator_status.value
        )

        return {"status": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# Endpoint to get an actuator status by actuator ID
# @router.get("/actuator-command-status/{actuator_id}", response_model=ActuatorStatus)
# async def get_actuator_status_by_actuator_id(actuator_id: str):
#     status = await actuator_status_service.get_actuator_status_by_actuator_id(actuator_id)
#     if status is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Actuator status for actuator with ID {actuator_id} not found."
#         )
#     return status

@router.get("/actuator-command-status/{actuator_id}", response_model=ActuatorStatus)
async def get_actuator_status_by_actuator_id(
    actuator_id: str,
    user = Depends(get_current_user),
    lab_service = Depends(get_lab_service)
):
    try:
        user_id = str(user["user_id"])

        actuator_status = await actuator_status_service.get_actuator_status_by_actuator_id(
            actuator_id
        )

        if actuator_status is None:
            raise HTTPException(
                status_code=404,
                detail=f"Actuator status for actuator {actuator_id} not found."
            )

        actuator = await actuator_service.get_actuator_by_id(actuator_id)

        if not actuator:
            raise HTTPException(
                status_code=404,
                detail="Actuator not found"
            )

        lab = await lab_service.get_lab_by_id(actuator["farmId"])

        if not lab:
            raise HTTPException(
                status_code=404,
                detail="Lab not found"
            )

        allowed = await can_access_farm(user_id, lab)

        if not allowed:
            raise HTTPException(
                status_code=403,
                detail="You are not allowed to view this actuator status"
            )

        return actuator_status

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# @router.get("/history/{actuator_id}/status", response_model=dict)
# async def get_actuator_status(
#     actuator_id: str,
#     page: int = Query(1, ge=1, description="Page number (starts from 1)"),
#     limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
# ):
   
#     result = await actuator_status_service.get_actuator_history_status_by_actuator_id(
#         actuator_id=actuator_id,
#         page=page,
#         limit=limit
#     )

#     if not result["items"]:
#         raise HTTPException(status_code=404, detail="No actuator status found")

#     return {
#         "actuator_id": actuator_id,
#         "page": result["page"],
#         "limit": result["limit"],
#         "total": result["total"],
#         "total_pages": result["total_pages"],
#         "items": [r.model_dump() for r in result["items"]]
#     }

@router.get("/history/{actuator_id}/status", response_model=dict)
async def get_actuator_status(
    actuator_id: str,
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    user = Depends(get_current_user),
    lab_service = Depends(get_lab_service)
):
    try:
        user_id = str(user["user_id"])

        actuator = await actuator_service.get_actuator_by_id(actuator_id)

        if not actuator:
            raise HTTPException(
                status_code=404,
                detail="Actuator not found"
            )

        lab = await lab_service.get_lab_by_id(actuator["farmId"])

        if not lab:
            raise HTTPException(
                status_code=404,
                detail="Lab not found"
            )

        allowed = await can_access_farm(user_id, lab)

        if not allowed:
            raise HTTPException(
                status_code=403,
                detail="You are not allowed to access actuator history"
            )

        result = await actuator_status_service.get_actuator_history_status_by_actuator_id(
            actuator_id=actuator_id,
            page=page,
            limit=limit
        )

        if not result["items"]:
            raise HTTPException(
                status_code=404,
                detail="No actuator status found"
            )

        return {
            "actuator_id": actuator_id,
            "page": result["page"],
            "limit": result["limit"],
            "total": result["total"],
            "total_pages": result["total_pages"],
            "items": [r.model_dump() for r in result["items"]]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )