from app.db.clients import mongodb
from app.models.sensors import Sensor,RegisterSensor,ResponseSensor
from fastapi import HTTPException
from bson.objectid import ObjectId
from datetime import datetime, timezone
from typing import List,Optional
from pymongo import MongoClient
import re


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
            
    async def get_latest_sensor_data(self, sensor_id: str):
        try:
            collection = self.get_collection()
            sensor_data = await collection.find_one(
                    {"sensor_id": sensor_id},
                    sort=[("timestamp", -1)]
                )
            if not sensor_data:
                    raise HTTPException(status_code=404, detail="Sensor data not found")

            sensor_data["id"] = str(sensor_data["_id"])
            return sensor_data

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving sensor data: {str(e)}")
        
    async def get_recent_sensor_data(self, sensor_id: str):
        try:
            collection = self.get_collection()

            cursor = collection.find(
                {"sensor_id": sensor_id}
            ).sort("timestamp", -1).limit(25)

            sensor_data = await cursor.to_list(length=25)

            if not sensor_data:
                raise HTTPException(status_code=404, detail="Sensor data not found")
            
            for doc in sensor_data:
                doc["id"] = str(doc["_id"])
                del doc["_id"]

            return sensor_data

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving sensor data: {str(e)}")



class SensorService:
    def __init__(self):
        self.collection_name = "sensors"

    def get_collection(self):
        return mongodb.db[self.collection_name] 


    async def create_sensor(self, sensor_data: RegisterSensor) -> ResponseSensor:
        collection = self.get_collection()
        sensor_dict = sensor_data.model_dump()
        existing = await collection.find_one({
            "farm_id": sensor_dict["farm_id"],
            "sensor_name": re.compile(f"^{re.escape(sensor_dict['sensor_name'])}$", re.IGNORECASE)
        })

        if existing:
            existing["id"] = str(existing["_id"])
            return ResponseSensor(**existing)

        result = await collection.insert_one(sensor_dict)
        sensor_dict["id"] = str(result.inserted_id)

        return ResponseSensor(**sensor_dict)


    async def list_sensors(self, skip: int = 0, limit: int = 10) -> List[ResponseSensor]:
            collection = self.get_collection()
            cursor = collection.find().skip(skip).limit(limit)
            docs = await cursor.to_list(length=limit)
            sensors = []
            for doc in docs:
                doc["id"] = str(doc["_id"])
                sensors.append(ResponseSensor(**doc))

            return sensors


    # Get sensor by ID
    async def get_sensor(self, sensor_id: str) -> Optional[ResponseSensor]:
        collection = self.get_collection()
        doc =await collection.find_one({"_id": ObjectId(sensor_id)})
        if doc:
            doc['id']=str(doc['_id'])
            return ResponseSensor(**doc)
        return None
    
    async def get_sensors_by_farm(self, farm_id: str) -> List[ResponseSensor]:
        collection = self.get_collection()
        docs  =await collection.find({"farm_id": farm_id}).to_list()
        for doc in docs:
            doc['id']=str(doc['_id'])
        return [ResponseSensor(**doc) for doc in docs]

    # Update sensor by ID
    async def update_sensor(self, sensor_id: str, updated_data: dict) -> Optional[ResponseSensor]:
        collection = self.get_collection()
        result = collection.update_one(
            {"_id": ObjectId(sensor_id)},
            {"$set": updated_data}
        )
        if result.modified_count:
            return self.get_sensor(sensor_id)
        return None

    def delete_sensor(self, sensor_id: str) -> bool:
        client: MongoClient = mongodb.client
        sensors_collection = self.get_collection()
        history_collection = mongodb.db[COLLECTION_NAME]

        with client.start_session() as session:
            with session.start_transaction():
                # Delete the sensor
                result = sensors_collection.delete_one({"_id": ObjectId(sensor_id)}, session=session)
                if result.deleted_count == 0:
                    # Sensor not found, abort transaction
                    session.abort_transaction()
                    return False
                # Delete all related sensor values/history
                history_collection.delete_many({"sensor_id": sensor_id}, session=session)

        return True
