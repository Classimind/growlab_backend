from fastapi import APIRouter, HTTPException, status,Query,Depends
from typing import List
from bson import ObjectId
from app.models import user
from app.models.sensors import RegisterSensor,ResponseSensor
from app.services.sensor_service import SensorService  
from app.core.auth_identity import get_current_user
from app.core.dependencies import  can_access_farm
from app.api.v1.farm import get_lab_service  

router = APIRouter(prefix="/sensors", tags=["Sensors"])
def get_sensor_service():
    return SensorService()



# @router.post("/", response_model=ResponseSensor, status_code=status.HTTP_201_CREATED)
# async def create_sensor(sensor: RegisterSensor):
#     try:
#         return await sensor_service.create_sensor(sensor)
#     except Exception as e:
#         raise HTTPException(status_code=500,detail=f'Unexpected error: {e}')

@router.post("/", response_model=ResponseSensor, status_code=status.HTTP_201_CREATED)
async def create_sensor(
    sensor: RegisterSensor,
    user=Depends(get_current_user),
    sensor_service: SensorService = Depends(get_sensor_service),
    lab_service=Depends(get_lab_service)
):
    try:
        sensor.created_by = user['user_id']
        lab = await lab_service.get_lab_by_id(sensor.lab_id)
        if not lab:
            raise HTTPException(status_code=404, detail="Lab not found")
        if not can_access_farm(user, lab, "create"):
            raise HTTPException(
                status_code=403,
                detail="You are not allowed to create sensor data for this farm"
            )
        return await sensor_service.create_sensor(sensor)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {e}"
        )



# @router.get("/", response_model=List[ResponseSensor])
# async def list_sensors(
#     page: int = Query(1, ge=1, description="Page number (starting from 1)"),
#     limit: int = Query(10, gt=0, le=100, description="Number of records per page")
# ):
#     skip = (page - 1) * limit
#     sensors = await sensor_service.list_sensors(skip=skip, limit=limit)
#     return sensors

@router.get("/", response_model=List[ResponseSensor])
async def list_sensors(
    lab_id: str = Query(..., description="Lab ID required to filter sensors"),
    user=Depends(get_current_user),
    lab_service=Depends(get_lab_service),
    sensor_service: SensorService = Depends(get_sensor_service)
):
    try:
        print(f"Received lab_id: {lab_id}")
        lab = await lab_service.get_lab_by_id(lab_id)

        if not lab:
            raise HTTPException(status_code=404, detail="Lab not found")

        if not can_access_farm(user, lab, "read"):
            raise HTTPException(status_code=403, detail="No farm access")

        sensors = await sensor_service.get_sensors_by_farm(lab_id)

        return sensors

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching sensors: {e}"
        )


# @router.get("/{sensor_id}", response_model=ResponseSensor)
# async def get_sensor(sensor_id: str):
#     if not ObjectId.is_valid(sensor_id):
#         raise HTTPException(status_code=400, detail="Invalid sensor ID format")

#     sensor =await sensor_service.get_sensor(sensor_id)
#     if not sensor:
#         raise HTTPException(status_code=404, detail="Sensor not found")
#     return sensor

@router.get("/{sensor_id}", response_model=ResponseSensor)
async def get_sensor(
    sensor_id: str,
    user=Depends(get_current_user),
    sensor_service: SensorService = Depends(get_sensor_service),
    lab_service=Depends(get_lab_service)
):
    try:
        if not ObjectId.is_valid(sensor_id):
            raise HTTPException(status_code=400, detail="Invalid sensor ID format")

        sensor = await sensor_service.get_sensor(sensor_id)

        if not sensor:
            raise HTTPException(status_code=404, detail="Sensor not found")

        lab = await lab_service.get_lab_by_id(sensor.lab_id)

        if not lab:
            raise HTTPException(status_code=404, detail="Lab not found")

        if not can_access_farm(user, lab, "read"):
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access this sensor"
            )

        return sensor

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving sensor: {e}"
        )


# @router.get("/farm/{farm_id}", response_model=List[RegisterSensor])
# async def get_sensors_by_farm(farm_id: str):
#     sensors =await sensor_service.get_sensors_by_farm(farm_id)
#     return sensors

@router.get("/farm/{farm_id}", response_model=List[RegisterSensor])
async def get_sensors_by_farm(
    farm_id: str,
    user=Depends(get_current_user),
    lab_service=Depends(get_lab_service),
    sensor_service: SensorService = Depends(get_sensor_service)
):
    try:
   
        lab = await lab_service.get_lab_by_id(farm_id)

        if not lab:
            raise HTTPException(status_code=404, detail="Farm not found")


        if not can_access_farm(user, lab, "read"):
            raise HTTPException(
                status_code=403,
                detail="You do not have access to this farm"
            )


        sensors = await sensor_service.get_sensors_by_farm(farm_id)

        return sensors

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching sensors: {e}"
        )


# @router.put("/{sensor_id}", response_model=ResponseSensor)
# async def update_sensor(sensor_id: str, updated_data: dict):
#     if not ObjectId.is_valid(sensor_id):
#         raise HTTPException(status_code=400, detail="Invalid sensor ID format")

#     updated = sensor_service.update_sensor(sensor_id, updated_data)
#     if not updated:
#         raise HTTPException(status_code=404, detail="Sensor not found or no changes made")

#     updated._id = str(updated._id)
#     return updated

@router.put("/{sensor_id}", response_model=ResponseSensor)
async def update_sensor(
    sensor_id: str,
    updated_data: dict,
    user=Depends(get_current_user),
    sensor_service: SensorService = Depends(get_sensor_service),
    lab_service=Depends(get_lab_service)
):
    try:

        if not ObjectId.is_valid(sensor_id):
            raise HTTPException(status_code=400, detail="Invalid sensor ID format")

        sensor = await sensor_service.get_sensor(sensor_id)

        if not sensor:
            raise HTTPException(status_code=404, detail="Sensor not found")

        lab = await lab_service.get_lab_by_id(sensor.lab_id)

        if not lab:
            raise HTTPException(status_code=404, detail="Lab not found")

        if not can_access_farm(user, lab, "update"):
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to update this sensor"
            )
        
        protected_fields = ["_id", "sensor_id", "lab_id", "created_at"]
        for field in protected_fields:
            updated_data.pop(field, None)

        updated = await sensor_service.update_sensor(sensor_id, updated_data)

        if not updated:
            raise HTTPException(status_code=404, detail="Sensor not found or no changes made")

        updated._id = str(updated._id)

        return updated

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating sensor: {e}")


# @router.delete("/{sensor_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_sensor(sensor_id: str):
#     if not ObjectId.is_valid(sensor_id):
#         raise HTTPException(status_code=400, detail="Invalid sensor ID format")

#     deleted = sensor_service.delete_sensor(sensor_id)
#     if not deleted:
#         raise HTTPException(status_code=404, detail="Sensor not found")

#     return {"message": "Sensor and its history deleted successfully"}

@router.delete("/{sensor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sensor(
    sensor_id: str,
    user=Depends(get_current_user),
    sensor_service: SensorService = Depends(get_sensor_service),
    lab_service=Depends(get_lab_service)
):
    try:
        if not ObjectId.is_valid(sensor_id):
            raise HTTPException(status_code=400, detail="Invalid sensor ID format")

        sensor = await sensor_service.get_sensor(sensor_id)

        if not sensor:
            raise HTTPException(status_code=404, detail="Sensor not found")

        lab = await lab_service.get_lab_by_id(sensor.lab_id)

        if not lab:
            raise HTTPException(status_code=404, detail="Lab not found")

        if not can_access_farm(user, lab, "delete"):
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to delete this sensor"
            )

        deleted = await sensor_service.delete_sensor(sensor_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Sensor not found")

        return {"message": "Sensor and its history deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting sensor: {e}"
        )