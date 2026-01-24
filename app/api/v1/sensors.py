from fastapi import APIRouter,HTTPException
router = APIRouter()
from typing import List
from app.models.sensors import Sensor
from app.services.ws_connection_manager_sensor import sensormanager
from app.services.sensor_service import CollectSensorValueService
import asyncio

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
async def create_sensors_batch(sensors: List[Sensor]):
    try:
        # Save all sensors in batch
        await sensor_service.add_sensor_values_batch(sensors)

        # Send all updates concurrently
        tasks = [
            sensormanager.send_update(sensor.sensor_id, sensor.model_dump())
            for sensor in sensors
        ]
        await asyncio.gather(*tasks)

        # Return the saved sensors
        return sensors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving sensors: {str(e)}")



@router.get("/latest/{sensor_id}",response_model=Sensor)
async def get_latest_sensor(sensor_id: str):
    try:
        return await sensor_service.get_latest_sensor_data(sensor_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving latest sensor data: {str(e)}")



@router.get("/recent/{sensor_id}")
async def get_latest_sensor_data(sensor_id: str):
    try:
        data = await sensor_service.get_recent_sensor_data(sensor_id)
        return {"success": True, "count": len(data), "data": data}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sensor data: {str(e)}")