from app.db.clients import mongodb
from app.models.actuator import  ActuatorStatus,ResponseActuatorStatus
from typing import Optional
from fastapi import HTTPException

COLLECTION_NAME="actuator_states"

class ActuatorStatusService:

    def __init__(self):
        self.collection_name = COLLECTION_NAME

    def get_collection(self):
        return mongodb.db[COLLECTION_NAME]
    
    async def create_actuator_status(self, actuator_status: ActuatorStatus) -> ActuatorStatus:
        # Create a new actuator status
        collection = self.get_collection()
        status_data = actuator_status.model_dump()
        result = await collection.insert_one(status_data)
        status_data["_id"] = str(result.inserted_id)
        return ActuatorStatus(**status_data)
        
    async def get_actuator_status_by_actuator_id(self, actuator_id: str) -> Optional[ActuatorStatus]:
        # Get the latest actuator status by actuator ID
        collection = self.get_collection()
        status = await collection.find_one(
            {"actuator_id": actuator_id},
            sort=[("created", -1)]  
        )
        if status:
            return ActuatorStatus(**status)
        return None
    
    async def get_actuator_history_status_by_actuator_id(
        self,
        actuator_id: str,
        page: int = 1,
        limit: int = 10
    ) -> dict:
        """
        Get paginated actuator statuses by actuator ID.
        Returns a dict with items, total count, current page, total pages.
        """
        collection = self.get_collection()

        # Calculate pagination parameters
        skip = (page - 1) * limit

        # Query total count
        total = await collection.count_documents({"actuator_id": actuator_id})

        # Query paginated data
        cursor = collection.find(
            {"actuator_id": actuator_id},
            sort=[("created", -1)]
        ).skip(skip).limit(limit)

        results = [ResponseActuatorStatus.from_mongo(doc) async for doc in cursor]
        # Compute total pages
        total_pages = (total + limit - 1) // limit if total > 0 else 1

        return {
            "items": results,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }


    async def get_recent_actuators_data(self, limit: int = 25):
        """
        Get the latest actuator status for each actuator, including actuator name.
        Returns up to `limit` actuators.
        """
        try:
            collection = self.get_collection()  # actuator values collection

            pipeline = [
                # Sort newest first
                {"$sort": {"created": -1}},

                # Group by actuator_id, keep the latest document
                {
                    "$group": {
                        "_id": "$actuator_id",
                        "latest": {"$first": "$$ROOT"}
                    }
                },

                # Replace root with the latest document
                {"$replaceRoot": {"newRoot": "$latest"}},

                # Lookup actuator name from `actuators` collection using ObjectId
                {
                    "$lookup": {
                        "from": "actuators",
                        "let": {"actuator_id_str": "$actuator_id"},
                        "pipeline": [
                            {
                                "$match": {
                                    "$expr": {
                                        "$eq": ["$_id", {"$toObjectId": "$$actuator_id_str"}]
                                    }
                                }
                            }
                        ],
                        "as": "actuator_info"
                    }
                },

                # Unwind the array from lookup
                {"$unwind": {"path": "$actuator_info", "preserveNullAndEmptyArrays": True}},

                # Add 'name' field; fallback to None if not found
                {
                    "$addFields": {
                        "name": {"$ifNull": ["$actuator_info.actuator_name", None]}
                    }
                },

                # Limit number of actuators returned
                {"$limit": limit},

                # Remove the lookup array field
                {"$project": {"actuator_info": 0}}
            ]

            cursor = collection.aggregate(pipeline)
            actuator_data = await cursor.to_list(length=limit)

            if not actuator_data:
                raise HTTPException(status_code=404, detail="No actuator data found")

            for doc in actuator_data:
                doc["id"] = str(doc["_id"])
                doc["actuator_id"] = str(doc["actuator_id"])
                # Remove _id since we added id
                del doc["_id"]

            return actuator_data

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving actuator data: {str(e)}"
            )
