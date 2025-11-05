from app.db.clients import mongodb
from app.models.sensors import Sensor
from fastapi import HTTPException
from uuid import uuid4
from datetime import datetime, timezone
from typing import List

COLLECTION_NAME = "sensors_values"

class CollectSensorValueService:
    def __init__(self):
        self.collection_name = COLLECTION_NAME

    def get_collection(self):
        return mongodb.db[self.collection_name]


    async def add_sensor_value(self, sensor: Sensor):
        """
        Store a single sensor value.
        """
        try:
            collection = self.get_collection()  # Get collection object
            data = sensor.model_dump()
            if "created" not in data or data["created"] is None:
                data["created"] = datetime.now(timezone.utc)
            await collection.insert_one(data)
            return data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error inserting sensor data: {str(e)}")

    async def add_sensor_values_batch(self, sensors: List[Sensor]):
        """
        Store multiple sensor values at once (batch insert).
        """
        try:
            collection = self.get_collection()  # Get collection object
            documents = []
            for sensor in sensors:
                data = sensor.model_dump()
                if "created" not in data or data["created"] is None:
                    data["created"] = datetime.now(timezone.utc)
                documents.append(data)

            if documents:
                result = await collection.insert_many(documents)
                return {"inserted_ids": [str(_id) for _id in result.inserted_ids]}
            return {"inserted_ids": []}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error inserting batch sensor data: {str(e)}")
        
    async def get_all_sensors(self, limit: int = 100):
        """Get all sensor values (limited)."""
        try:
            collection = self.get_collection()  # Get collection object
            sensors = await collection.find().to_list(limit)
            return sensors
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching sensor data: {str(e)}")

    async def get_sensors_by_farm(self, farm_id: str, limit: int = 100):
        """Get sensor values for a specific farm."""
        try:
            collection = self.get_collection()  # Get collection object
            sensors = await collection.find({"farm_id": farm_id}).to_list(limit)
            return sensors
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching sensor data for farm {farm_id}: {str(e)}")

    async def get_sensors_by_date_range(self, start: datetime, end: datetime, limit: int = 100):
        """Get sensor values within a specific date range."""
        try:
            collection = self.get_collection()  # Get collection object
            sensors = await collection.find(
                {"created": {"$gte": start, "$lte": end}}
            ).to_list(limit)
            return sensors
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching sensor data for date range: {str(e)}")

    async def get_sensors_by_farm_and_date_range(self, farm_id: str, start: datetime, end: datetime, limit: int = 100):
        """Get sensor values for a farm within a specific date range."""
        try:
            collection = self.get_collection()  # Get collection object
            sensors = await collection.find(
                {
                    "farm_id": farm_id,
                    "created": {"$gte": start, "$lte": end}
                }
            ).to_list(limit)
            return sensors
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching sensor data for farm {farm_id} in date range: {str(e)}")

    async def get_sensors_by_name_and_farm(self, sensor_name: str, farm_id: str, limit: int = 100):
        try:
            collection = self.get_collection()
            cursor = collection.find({"sensor_name": sensor_name, "farm_id": farm_id}).limit(limit)
            sensors = []
            async for doc in cursor:
                # Convert ObjectId to string
                doc["_id"] = str(doc["_id"])
                sensors.append(doc)
            return sensors
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching sensor data for sensor '{sensor_name}' in farm '{farm_id}': {str(e)}"
            )

