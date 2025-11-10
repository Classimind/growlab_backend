from fastapi import APIRouter, HTTPException, status,Query
from typing import List
from bson import ObjectId
from app.models.sensors import RegisterSensor,ResponseSensor
from app.services.sensor_service import SensorService    

router = APIRouter(prefix="/sensors", tags=["Sensors"])
sensor_service = SensorService()



@router.post("/", response_model=ResponseSensor, status_code=status.HTTP_201_CREATED)
async def create_sensor(sensor: RegisterSensor):
    try:
        return await sensor_service.create_sensor(sensor)
    except Exception as e:
        raise HTTPException(status_code=500,detail=f'Unexpected error: {e}')



@router.get("/", response_model=List[ResponseSensor])
async def list_sensors(
    page: int = Query(1, ge=1, description="Page number (starting from 1)"),
    limit: int = Query(10, gt=0, le=100, description="Number of records per page")
):
    skip = (page - 1) * limit
    sensors = await sensor_service.list_sensors(skip=skip, limit=limit)
    return sensors



@router.get("/{sensor_id}", response_model=ResponseSensor)
async def get_sensor(sensor_id: str):
    if not ObjectId.is_valid(sensor_id):
        raise HTTPException(status_code=400, detail="Invalid sensor ID format")

    sensor =await sensor_service.get_sensor(sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return sensor



@router.get("/farm/{farm_id}", response_model=List[RegisterSensor])
async def get_sensors_by_farm(farm_id: str):
    sensors =await sensor_service.get_sensors_by_farm(farm_id)
    return sensors



@router.put("/{sensor_id}", response_model=ResponseSensor)
async def update_sensor(sensor_id: str, updated_data: dict):
    if not ObjectId.is_valid(sensor_id):
        raise HTTPException(status_code=400, detail="Invalid sensor ID format")

    updated = sensor_service.update_sensor(sensor_id, updated_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Sensor not found or no changes made")

    updated._id = str(updated._id)
    return updated



@router.delete("/{sensor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sensor(sensor_id: str):
    if not ObjectId.is_valid(sensor_id):
        raise HTTPException(status_code=400, detail="Invalid sensor ID format")

    deleted = sensor_service.delete_sensor(sensor_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Sensor not found")

    return {"message": "Sensor and its history deleted successfully"}
