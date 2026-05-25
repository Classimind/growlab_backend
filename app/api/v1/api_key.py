from fastapi import APIRouter, Depends, Header, HTTPException
from app.services.api_key_service import APIKeyService
from app.models.api_key import APIKeyCreateRequest
from app.db.clients import get_db
from app.core.auth_identity import get_current_user
from app.core.dependencies import  can_access_farm
from app.api.v1.farm import get_lab_service
from fastapi import Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/api-keys", tags=["API Keys"])

def get_service(db: AsyncIOMotorDatabase = Depends(get_db)):
    return APIKeyService(db)


@router.post("/create")
async def create_api_key(
    payload: APIKeyCreateRequest,
    user=Depends(get_current_user),
    service: APIKeyService = Depends(get_service),
    lab_service=Depends(get_lab_service)
):

    lab = await lab_service.get_lab_by_id(payload.lab_id)

    if not lab:
        raise HTTPException(
            status_code=404,
            detail="Lab not found"
        )

    if not can_access_farm(user=user,lab=lab,action="create"):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to create in this lab"
        )
 
    return await service.create_api(
        userId=user["user_id"],
        payload=payload
    )

@router.get("/lab/{lab_id}")
async def get_api_keys_by_lab(
    lab_id: str,
    user=Depends(get_current_user),
    service: APIKeyService = Depends(get_service),
    lab_service=Depends(get_lab_service)
):

    lab = await lab_service.get_lab_by_id(lab_id)

    if not lab:
        raise HTTPException(
            status_code=404,
            detail="Lab not found"
        )

    if not can_access_farm(user=user, lab=lab, action="read"):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to view API keys in this lab"
        )

    return await service.get_api_keys_by_lab(lab_id=lab_id)


@router.delete("/revoke")
async def revoke_api_key(
    key_id: str = Query(...),
    lab_id: str = Query(...),
    user=Depends(get_current_user),
    service: APIKeyService = Depends(get_service),
    lab_service=Depends(get_lab_service),
):
    # 1. Fetch lab (still useful for validation context)
    lab = await lab_service.get_lab_by_id(lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")

    # 2. Fetch API key
    api_key = await service.get_api_by_id(key_id)

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    # 3. Ensure key belongs to lab (multi-tenant safety)
    if api_key.get("lab_id") != lab_id:
        raise HTTPException(
            status_code=403,
            detail="API key does not belong to this lab"
        )
    
    if api_key.get("user_id","") != str(user["user_id"]):
        raise HTTPException(
            status_code=403,
            detail="Only the owner can revoke this API key"
        )


    success = await service.revoke_api(key_id)
    print(success)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to revoke API key")

    return {
        "message": "API key revoked successfully",
        "lab_id": lab_id,
        "key_id": key_id
    }
