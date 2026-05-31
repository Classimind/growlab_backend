from fastapi import APIRouter, Depends, HTTPException

from app.db.clients import get_db
from app.db.device_repo import DeviceRepository
from app.services.device_service import DeviceService
from app.models.device import DeviceStatusIn
from app.core.auth_identity import get_current_user


router = APIRouter(prefix="/device", tags=["Device"])



def get_repo(db=Depends(get_db)):
    return DeviceRepository(db)


def get_service(repo=Depends(get_repo)):
    return DeviceService(repo)



@router.post("/status")
async def update_status(
    payload: DeviceStatusIn,
    user=Depends(get_current_user),
    service: DeviceService = Depends(get_service)
):
    return await service.update_status(payload)



@router.get("/{device_id}")
async def get_device(
    device_id: str,
    user=Depends(get_current_user),
    service: DeviceService = Depends(get_service)
):
    device = await service.get_device(device_id)

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return device


@router.get("/all")
async def list_devices(service: DeviceService = Depends(get_service)):
    return await service.list_devices()



@router.get("/farm/{farm_id}")
async def get_farm_devices(
    farm_id: str,
    user=Depends(get_current_user),
    service: DeviceService = Depends(get_service)
):
    return await service.get_farm_devices(farm_id)



@router.delete("/{device_id}")
async def delete_device(
    device_id: str,
    user=Depends(get_current_user),
    repo=Depends(get_repo)
):
    result = await repo.collection.delete_one({"deviceId": device_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Device not found")

    return {
        "success": True,
        "message": f"Device {device_id} deleted"
    }



@router.get("/ping/{device_id}")
async def ping_device(
    device_id: str,
    user=Depends(get_current_user),
    service: DeviceService = Depends(get_service)
):
    device = await service.get_device(device_id)

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return {
        "deviceId": device_id,
        "status": "alive",
        "is_online": device["is_online"]
    }