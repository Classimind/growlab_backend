from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.farm import Lab
from app.services.lab_service import LabService
from app.db.clients import get_db

from app.core.dependencies import get_current_user
from app.core.roles import FarmRole,Role

farm_router = APIRouter(prefix="/labs", tags=["Labs"])



def get_lab_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> LabService:
    return LabService(db)


def require_roles(allowed_roles: list[Role,FarmRole]):
    def dependency(user=Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Permission denied"
            )
        return user
    return dependency


# ---------------- ROUTES ----------------

@farm_router.post("/")
async def create_lab(
    lab: Lab,
    service: LabService = Depends(get_lab_service),
    user=Depends(require_roles([Role.USER,Role.ADMIN,Role.SUPER_ADMIN,Role.RESEARCHER]))
):
    lab.created_by = str(user.id)
    return await service.create_lab(lab)


@farm_router.get("/")
async def get_all_labs(
    service: LabService = Depends(get_lab_service),
    user=Depends(get_current_user)
):
    return await service.get_all_labs()


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