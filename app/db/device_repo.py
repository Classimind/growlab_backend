from app.db.clients import mongodb


class DeviceRepository:
    def __init__(self,db):
        self.device_collection = db["devices"]

    async def upsert(self, device_id: str, data: dict):
        return await self.device_collection.update_one(
            {"deviceId": device_id},
            {"$set": data},
            upsert=True
        )

    def get_by_farm(self, farm_id: str):
        return  self.device_collection.find({"farmId": farm_id})

    def get_one(self, device_id: str):
        return  self.device_collection.find_one({"deviceId": device_id})

    def list_all(self):
        return  self.device_collection.find()