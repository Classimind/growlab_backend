from fastapi import APIRouter, Depends, HTTPException,status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.farm import Lab
from app.services.lab_service import LabService
from app.db.clients import get_db
from pymongo.errors import PyMongoError
from app.core.auth_identity import get_current_user
from app.core.dependencies import  can_access_farm
from app.core.roles import FarmRole,Role
from app.core.dependencies import require_roles
from bson import ObjectId
farm_router = APIRouter()



def get_lab_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> LabService:
    return LabService(db)


@farm_router.post("/")
async def create_lab(
    lab: Lab,
    service: LabService = Depends(get_lab_service),
    user=Depends(require_roles([Role.USER,Role.ADMIN,Role.SUPER_ADMIN,Role.RESEARCHER]))
):

    lab.created_by = str(user['user_id'])
    return await service.create_lab(lab)


@farm_router.get("/")
async def get_all_labs(
    service: LabService = Depends(get_lab_service),
    user=Depends(get_current_user),
):
    try:
        user_id = ObjectId(user["user_id"])

        query = {
            "$or": [
                {"created_by": user_id},
                {"employees.user_id": user_id},
            ]
        }
        return await service.get_all_labs(query)

    except PyMongoError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error",
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong",
        )


@farm_router.get("/{lab_id}")
async def get_lab_by_id(
    lab_id: str,
    service: LabService = Depends(get_lab_service),
    user=Depends(get_current_user)
):
    lab = await service.get_lab_by_id(lab_id)

    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")

    return lab


@farm_router.put("/{lab_id}")
async def update_lab(
    lab_id: str,
    update_data: dict,
    service: LabService = Depends(get_lab_service),
    user=Depends(require_roles([FarmRole.OWNER, FarmRole.ADMIN]))
):
    return await service.update_lab(lab_id, update_data)


@farm_router.delete("/{lab_id}")
async def delete_lab(
    lab_id: str,
    service: LabService = Depends(get_lab_service),
    user=Depends(require_roles([FarmRole.OWNER]))
):
    return await service.delete_lab(lab_id)