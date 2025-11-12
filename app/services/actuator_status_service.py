from app.db.clients import mongodb
from app.models.actuator import  ActuatorStatus,ResponseActuatorStatus
from typing import Optional

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

