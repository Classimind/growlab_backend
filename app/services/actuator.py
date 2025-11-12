from app.models.actuator import Actuator, ResponseActuator
from typing import List, Optional
from bson import ObjectId
from fastapi import HTTPException, status
from app.db.clients import mongodb


COLLECTION_NAME='actuators'
class ActuatorService:
    def __init__(self):
        self.collection_name = COLLECTION_NAME

    def get_collection(self):
        return mongodb.db[self.collection_name]


    async def create_actuator(self, actuator: Actuator) -> tuple:
        collection = self.get_collection()

        # Check if actuator already exists by farmId + actuator_name
        existing_actuator = await collection.find_one({
            "farmId": actuator.farmId,
            "actuator_name": actuator.actuator_name
        })
        if existing_actuator:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Actuator '{actuator.actuator_name}' already exists in farm '{actuator.farmId}'."
            )

        # Convert the actuator model to a dictionary for insertion
        actuator_dict = actuator.model_dump()  # Pydantic model to dict

        # Insert the new actuator into the collection
        result = await collection.insert_one(actuator_dict)

        # Check if the insertion was successful (result should contain inserted_id)
        if result.inserted_id:
            return (True,result.inserted_id)
        return (False,None)


    async def ensure_unique_index(self):
        collection = self.get_collection()
        """Ensures that there is a unique index on farmId and actuator_name"""
        await collection.create_index([("farmId", 1), ("actuator_name", 1)], unique=True)

    async def get_actuator_by_id(self, actuator_id: str) -> Optional[ResponseActuator]:
        # Fetch an actuator by its ID
        collection = self.get_collection()
        actuator = await collection.find_one({"_id": ObjectId(actuator_id)})
        actuator=ResponseActuator.from_mongo(actuator)
        if actuator:
            return actuator
        return None

    async def get_all_actuators(self, farm_id: Optional[str] = None) -> List[ResponseActuator]:
        # Fetch all actuators or filter by farmId
        collection = self.get_collection()
        query = {}
        if farm_id:
            query["farmId"] = farm_id
        actuators = []
        async for actuator in collection.find(query):
            actuators.append(ResponseActuator.from_mongo(actuator))
        return actuators

    async def update_actuator(self, actuator_id: str, actuator_update: Actuator) -> Optional[ResponseActuator]:
        # Update an actuator by its ID
        collection = self.get_collection()
        update_data = actuator_update.model_dump(exclude_unset=True)  # Exclude unset fields to only update provided fields
        result = await collection.update_one(
            {"_id": ObjectId(actuator_id)}, {"$set": update_data}
        )
        if result.modified_count > 0:
            updated_actuator = await self.get_actuator_by_id(actuator_id)
            return updated_actuator
        return None

    async def delete_actuator(self, actuator_id: str) -> bool:
        # Delete an actuator by its ID
        collection = self.get_collection()
        result = await collection.delete_one({"_id": ObjectId(actuator_id)})
        return result.deleted_count > 0
