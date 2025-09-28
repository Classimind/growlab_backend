from db.clients import mongodb
from models.actuator_status_history import ActuatorStatusHistory


COLLECTION_NAME="actuator_states"

class ActuatorStatusService:

    def __init__(self):
        self.collection= mongodb.db[COLLECTION_NAME]

    async def create_status(self,actuator_data:dict):
        data = ActuatorStatusHistory(**actuator_data)
        result = await self.collection.insert_one(data.model_dump())
        return str(result.inserted_id)
    
    async def get_last_status(self,actuator_name:str,farm_name:str):
        data = await self.collection.find_one(
            {
                "actuator_name":actuator_name,
                "farm_name":farm_name,
            },
            sort=[("modified",-1)]
        )
        if data:
            return ActuatorStatusHistory(**data)
        return None
