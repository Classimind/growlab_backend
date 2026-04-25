from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.farm import Lab


def serialize_lab(lab: dict) -> dict:
    """
    Convert MongoDB document into JSON-safe dict
    Handles:
    - ObjectId → str
    - datetime → ISO format
    """

    if "_id" in lab:
        lab["_id"] = str(lab["_id"])

    for key, value in lab.items():
        if isinstance(value, datetime):
            lab[key] = value.isoformat()

    return lab


class LabService:

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db['labs']

    async def create_lab(self, lab: Lab) -> Dict[str, Any]:

        lab_dict = lab.model_dump()

        #  timestamp
        lab_dict["created_at"] = datetime.now(timezone.utc)

        #  convert creator to ObjectId
        if lab_dict.get("created_by"):
            lab_dict["created_by"] = ObjectId(lab_dict["created_by"])

        # convert employees user_id → ObjectId
        if lab_dict.get("employees"):
            for emp in lab_dict["employees"]:
                if isinstance(emp.get("user_id"), str):
                    emp["user_id"] = ObjectId(emp["user_id"])

        result = await self.collection.insert_one(lab_dict)

        return {
            "success": True,
            "lab_id": str(result.inserted_id),
            "message": "Lab created successfully"
        }


    async def get_all_labs(self) -> List[Dict[str, Any]]:

        labs = []
        cursor = self.collection.find()

        async for lab in cursor:
            labs.append(serialize_lab(lab))

        return labs


    async def get_lab_by_id(self, lab_id: str) -> Optional[Dict[str, Any]]:

        if not ObjectId.is_valid(lab_id):
            return None

        lab = await self.collection.find_one({"_id": ObjectId(lab_id)})

        return serialize_lab(lab) if lab else None

    async def update_lab(self, lab_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:

        if not ObjectId.is_valid(lab_id):
            return {"success": False, "message": "Invalid lab ID"}

        # timestamp
        update_data["updated_at"] = datetime.now(timezone.utc)

        # convert created_by if present
        if "created_by" in update_data:
            update_data["created_by"] = ObjectId(update_data["created_by"])

        # convert employees if present
        if "employees" in update_data:
            for emp in update_data["employees"]:
                if isinstance(emp.get("user_id"), str):
                    emp["user_id"] = ObjectId(emp["user_id"])

        result = await self.collection.update_one(
            {"_id": ObjectId(lab_id)},
            {"$set": update_data}
        )

        return {
            "success": result.modified_count > 0,
            "message": "Lab updated" if result.modified_count else "No changes made"
        }

    async def delete_lab(self, lab_id: str) -> Dict[str, Any]:

        if not ObjectId.is_valid(lab_id):
            return {"success": False, "message": "Invalid lab ID"}

        result = await self.collection.delete_one({"_id": ObjectId(lab_id)})

        return {
            "success": result.deleted_count > 0,
            "message": "Lab deleted" if result.deleted_count else "Lab not found"
        }


        if not ObjectId.is_valid(lab_id):
            return None

        lab = await self.collection.find_one({"_id": ObjectId(lab_id)})

        if not lab:
            return None

        return {
            "lab_id": str(lab["_id"]),
            "target_plant": lab.get("target_plant"),
            "preference": lab.get("preference"),

            # 🤖 RL state placeholder (sensor system will fill this)
            "state": {
                "ph": None,
                "ec": None,
                "temperature": None,
                "humidity": None
            }
        }