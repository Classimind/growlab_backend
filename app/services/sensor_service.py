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
        
    async def get_latest_sensor_data_by_farm(self, farm_id: str):
        try:
            sensor_values = self.get_collection()
            

            pipeline = [
                # 1. Filter by farm
                {
                    "$match": {"lab_id": farm_id}
                },

                # 2. Sort so we can pick latest value per sensor
                {
                    "$sort": {"created": -1}
                },

                # 3. Keep only latest record per sensor_id
                {
                    "$group": {
                        "_id": "$sensor_id",
                        "latest_value": {"$first": "$value"},
                        "created": {"$first": "$created"},
                        "lab_id": {"$first": "$lab_id"}
                    }
                },

                # 4. Join with sensors collection
                {
                    "$lookup": {
                        "from": "sensors",
                        "localField": "_id",
                        "foreignField": "sensor_id",
                        "as": "sensors"
                    }
                },

                # 5. Flatten sensor info
                {
                    "$unwind": {
                        "path": "$sensors",
                        "preserveNullAndEmptyArrays": True
                    }
                },

                # 6. Format output
                {
                    "$project": {
                        "_id": 0,
                        "sensor_id": "$_id",
                        "value": "$latest_value",
                        "created": 1,
                        "lab_id": 1,
                        "sensor_name": "$sensors.name",
                        "sensor_type": "$sensors.type",
                        "unit": "$sensors.unit"
                    }
                }
            ]

            result = await sensor_values.aggregate(pipeline).to_list(length=100)

            if not result:
                raise HTTPException(status_code=404, detail="No sensors found for this farm")

            return result

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching farm sensors: {str(e)}"
            )


    async def get_recent_sensors_data(self, limit: int = 25):
        """
        Get latest sensor readings per sensor_id, including the sensor name
        """
        try:
            collection = self.get_collection()  # sensors_values collection

            pipeline = [
                # Sort newest first
                {"$sort": {"created": -1}},

                # Group by sensor_id to get latest reading per sensor
                {
                    "$group": {
                        "_id": "$sensor_id",
                        "latest": {"$first": "$$ROOT"}
                    }
                },

                # Replace root with the latest reading
                {"$replaceRoot": {"newRoot": "$latest"}},

                # Lookup sensor name from `sensors` collection using ObjectId conversion
                {
                    "$lookup": {
                        "from": "sensors",
                        "let": {"sensor_id_str": "$sensor_id"},  # pass the string
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {
                                        "$eq": ["$_id", 
                                                
                                                # {"$toObjectId": "$$sensor_id_str"}
                                                 {
                                    "$convert": {
                                        "input": "$$sensor_id_str",
                                        "to": "objectId",
                                        "onError": None,
                                        "onNull": None
                                    }
                                }
                                                
                                                ]
                                    }
                                }
                            }
                        ],
                        "as": "sensor_info"
                    }
                },

                # Unwind the array from lookup
                {"$unwind": {"path": "$sensor_info", "preserveNullAndEmptyArrays": True}},

                # Add 'name' field; fallback to None if not found
                {
                    "$addFields": {
                        "name": {"$ifNull": ["$sensor_info.sensor_name", None]}
                    }
                },

                # Optionally limit the number of sensors
                {"$limit": limit},

                # Remove the lookup array field
                {"$project": {"sensor_info": 0}}
            ]

            cursor = collection.aggregate(pipeline)
            sensor_data = await cursor.to_list(length=limit)

            for doc in sensor_data:
                doc["id"] = str(doc["_id"])
                doc["sensor_id"] = str(doc["sensor_id"])
                # Remove _id since we added id
                # doc['_id']= str(doc["_id"])
                del doc['_id']
                # doc['created'] = str(doc['created'].strftime("%Y-%m-%d %H:%M:%S"))
            print(sensor_data)
            return sensor_data

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving sensor data with names: {str(e)}"
            )



class SensorService:
    def __init__(self):
        self.collection_name = "sensors"

    def get_collection(self):
        return mongodb.db[self.collection_name] 


    async def create_sensor(self, sensor_data: RegisterSensor) -> ResponseSensor:
        collection = self.get_collection()
        sensor_dict = sensor_data.model_dump()
        
        existing = await collection.find_one({
            "lab_id": sensor_dict["lab_id"],
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
        docs  =await collection.find({"lab_id": farm_id}).to_list()
        sensors = []
        for doc in docs:
            doc['id']=str(doc['_id'])
            sensors.append(ResponseSensor(**doc))
        return sensors

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
