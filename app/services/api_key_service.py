import secrets
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException
from app.models.api_key import APIKeyCreateRequest, APIKeyModel
from app.utilities.crypto_utils import generate_api_key,hash_api_key,verify_api_key

from app.core.permissions import FARM_ROLE_PERMISSIONS

class APIKeyService:

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["apis"]


    async def create_api(self, userId: str, payload: APIKeyCreateRequest):

        existing = await self.collection.find_one({
            "lab_id": payload.lab_id,
            "name": payload.name
        })
        

        if existing:
            raise HTTPException(
                status_code=400,
                detail="API key name already exists for this lab"
            )
        
        if payload.role not in FARM_ROLE_PERMISSIONS:
            raise HTTPException(
                status_code=400,
                detail="Invalid role"
            )
        permissions = list(FARM_ROLE_PERMISSIONS[payload.role])
        raw_key = generate_api_key()
        hashed_key = hash_api_key(raw_key)

        data = APIKeyModel(
            user_id=userId,
            lab_id=payload.lab_id,
            name=payload.name,
            hashed_key=hashed_key,
            permissions=permissions,
            is_active=True,
            created_at=datetime.now(),
            expires_at=payload.expires_at
        )

        result = await self.collection.insert_one(data.model_dump())
           
        return {
            "id": str(result.inserted_id),
            "api_key": raw_key,  # only shown once
            "name": payload.name,
            "lab_id": payload.lab_id,
            "permissions": permissions,
            "message": "API key created successfully"
        }
    
    async def get_api_keys_by_lab(self, lab_id: str):

        cursor = self.collection.find({"lab_id": lab_id})

        api_keys = []

        async for doc in cursor:
            api_keys.append({
                "id": str(doc["_id"]),
                "user_id": doc["user_id"],
                "lab_id": doc["lab_id"],
                "name": doc["name"],
                "permissions": doc["permissions"],
                "is_active": doc["is_active"],
                "created_at": doc["created_at"],
                "expires_at": doc.get("expires_at")
            })
        return {
            "lab_id": lab_id,
            "count": len(api_keys),
            "api_keys": api_keys
        }

    async def validate_api(self, raw_key: str):

        cursor = self.collection.find({"is_active": True})

        async for doc in cursor:

            # check expiry
            if doc.get("expires_at") and doc["expires_at"] < datetime.utcnow():
                continue

            # verify hash
            if verify_api_key(raw_key, doc["hashed_key"]):
                return doc

        return None


    async def revoke_api(self, raw_key: str):

        cursor = self.collection.find({"is_active": True})

        async for doc in cursor:

            if verify_api_key(raw_key, doc["hashed_key"]):

                await self.collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"is_active": False}}
                )

                return True

        return False