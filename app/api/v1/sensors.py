from fastapi import APIRouter,HTTPException,Depends
router = APIRouter()
from typing import List
from app.models.sensors import Sensor
from app.services.ws_connection_manager_sensor import sensormanager
from app.services.sensor_service import CollectSensorValueService,SensorService
import asyncio
from app.api.v1.farm import get_lab_service
from app.core.auth_identity import get_current_user
from app.core.dependencies import  can_access_farm

sensor_service = CollectSensorValueService()


def get_sensor_service():
    return SensorService()

# @router.post("/collect", response_model=Sensor)
# async def create_sensor(sensor: Sensor):
#     try:
#         await sensor_service.add_sensor_value(sensor)
#         data = sensor.model_dump()  
#         await sensormanager.send_update(sensor.sensor_id, data)
#         return sensor
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error saving sensor: {str(e)}")
    

@router.post("/collect", response_model=Sensor)
async def create_sensor(
    sensor: Sensor,
    user=Depends(get_current_user),
    lab_service=Depends(get_lab_service)
):
    try:
        lab = await lab_service.get_lab_by_id(sensor.lab_id)
        if not lab:
            raise HTTPException(status_code=404, detail="Lab not found")

        if not can_access_farm(user, lab, "create"):
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to create sensor data"
            )

        await sensor_service.add_sensor_value(sensor)

        data = sensor.model_dump()
        await sensormanager.send_update(sensor.sensor_id, data)

        return sensor

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving sensor: {str(e)}")


# @router.post("/collect/batch", response_model=List[Sensor])
# async def create_sensors_batch(sensors: List[Sensor]):
#     try:
#         # Save all sensors in batch
#         await sensor_service.add_sensor_values_batch(sensors)

#         # Send all updates concurrently
#         tasks = [
#             sensormanager.send_update(sensor.sensor_id, sensor.model_dump())
#             for sensor in sensors
#         ]
#         await asyncio.gather(*tasks)

#         # Return the saved sensors
#         return sensors
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error saving sensors: {str(e)}")


@router.post("/collect/batch", response_model=List[Sensor])
async def create_sensors_batch(
    sensors: List[Sensor],
    user=Depends(get_current_user),
    lab_service=Depends(get_lab_service)
):
    try:
        if not sensors:
            raise HTTPException(status_code=400, detail="No sensor data provided")
        lab_id = sensors[0].lab_id
        lab = await lab_service.get_lab_by_id(lab_id)
        if not lab:
            raise HTTPException(status_code=404, detail="Lab not found")

        for sensor in sensors:
            if sensor.lab_id != lab_id:
                raise HTTPException(
                    status_code=400,
                    detail="All sensors must belong to the same lab"
                )

        if not can_access_farm(user, lab, "create"):
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to create sensor data"
            )

        await sensor_service.add_sensor_values_batch(sensors)

        tasks = [
            sensormanager.send_update(sensor.sensor_id, sensor.model_dump())
            for sensor in sensors
        ]
        await asyncio.gather(*tasks)

        return sensors

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving sensors: {str(e)}")

# @router.get("/latest/{sensor_id}",response_model=Sensor)
# async def get_latest_sensor(sensor_id: str):
#     try:
#         return await sensor_service.get_latest_sensor_data(sensor_id)
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error retrieving latest sensor data: {str(e)}")


@router.get("/latest/{sensor_id}", response_model=Sensor)
async def get_latest_sensor(
    sensor_id: str,
    user=Depends(get_current_user),
    sensor_service=Depends(get_sensor_service),
    lab_service=Depends(get_lab_service)
):
    try:
        sensor = await sensor_service.get_sensor(sensor_id)

        if not sensor:
            raise HTTPException(status_code=404, detail="Sensor not found")

        lab = await lab_service.get_lab_by_id(sensor.lab_id)

        if not lab:
            raise HTTPException(status_code=404, detail="Lab not found")

        if not can_access_farm(user, lab, "read"):
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to view sensor data"
            )

        return await sensor_service.get_latest_sensor_data(sensor_id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @router.get("/recent/{sensor_id}")
# async def get_latest_sensor_data(sensor_id: str):
#     try:
#         data = await sensor_service.get_recent_sensor_data(sensor_id)
#         return {"success": True, "count": len(data), "data": data}
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching sensor data: {str(e)}")
    
@router.get("/recent/{sensor_id}")
async def get_recent_sensor_data(
    sensor_id: str,
    user=Depends(get_current_user),
    sensor_service=Depends(get_sensor_service),
    lab_service=Depends(get_lab_service)
):
    try:
      
        sensor = await sensor_service.get_sensor(sensor_id)

        if not sensor:
            raise HTTPException(status_code=404, detail="Sensor not found")

     
        lab = await lab_service.get_lab_by_id(sensor.lab_id)

        if not lab:
            raise HTTPException(status_code=404, detail="Lab not found")

      
        if not can_access_farm(user, lab, "read"):
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to view sensor data"
            )

        data = await sensor_service.get_recent_sensor_data(sensor_id)

        return {
            "success": True,
            "count": len(data),
            "data": data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
