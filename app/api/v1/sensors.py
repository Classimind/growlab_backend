from fastapi import APIRouter,HTTPException
router = APIRouter()
from typing import List
from app.models.sensors import Sensor
from app.services.ws_connection_manager_sensor import sensormanager
from app.services.sensor_service import CollectSensorValueService
from datetime import datetime

sensor_service = CollectSensorValueService()

@router.post("/collect", response_model=Sensor)
async def create_sensor(sensor: Sensor):
    try:
        await sensor_service.add_sensor_value(sensor)
        data = sensor.model_dump()  # returns dict
        await sensormanager.send_update(sensor.sensor_id, data)
        return sensor
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving sensor: {str(e)}")

@router.post("/collect/batch", response_model=List[Sensor])
async def create_sensors_batch(sensor: List[Sensor]):
    try:
        await sensor_service.add_sensor_values_batch(sensor)
        return sensor
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving sensor: {str(e)}")


@router.get("/", response_model=List[Sensor])
async def list_sensors():
    try:
        return await sensor_service.get_all_sensors()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/farm/{farm_id}", response_model=List[Sensor])
async def list_sensors_by_farm(farm_id: str):
    try:
        return await sensor_service.get_sensors_by_farm(farm_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/range/", response_model=List[Sensor])
async def list_sensors_by_date_range(start: datetime, end: datetime):
    try:
        return await sensor_service.get_sensors_by_date_range(start, end)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/farm/{farm_id}/range/", response_model=List[Sensor])
async def list_sensors_by_farm_and_date_range(farm_id: str, start: datetime, end: datetime):
    try:
        return await sensor_service.get_sensors_by_farm_and_date_range(farm_id, start, end)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    

@router.get("/farm/{farm_id}/sensor/{sensor_name}")
async def list_sensors_by_name_and_farm(farm_id: str, sensor_name: str):
    return await sensor_service.get_sensors_by_name_and_farm(sensor_name, farm_id)