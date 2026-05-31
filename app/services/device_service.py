from datetime import datetime, timezone
from app.core.config import settings
from app.db.device_repo import DeviceRepository


class DeviceService:

    def __init__(self, repo: DeviceRepository):
        self.repo = repo

    def _now(self):
        return datetime.now(timezone.utc)

    def _normalize_datetime(self, dt: datetime):
        if not dt:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    def _is_online(self, last_seen: datetime):
        last_seen = self._normalize_datetime(last_seen)

        if not last_seen:
            return False

        return (self._now() - last_seen).total_seconds() < settings.DEVICE_TIMEOUT_SEC


    def _serialize_device(self, device: dict):
        if not device:
            return None

        last_seen = self._normalize_datetime(device.get("last_seen"))

        device["_id"] = str(device.get("_id", ""))
        device["last_seen"] = last_seen
        device["is_online"] = self._is_online(last_seen)

        return device

    async def update_status(self, payload):
        now = self._now()

        data = payload.model_dump()
        data["last_seen"] = now

        await self.repo.upsert(payload.deviceId, data)

        return {
            "success": True,
            "deviceId": payload.deviceId,
            "farmId": payload.farmId,
            "last_seen": now,
        }


    async def get_device(self, device_id: str):
        device = await self.repo.get_one(device_id)

        if not device:
            return None

        return self._serialize_device(device)

    async def get_farm_devices(self, farm_id: str):
        cursor = self.repo.get_by_farm(farm_id)

        devices = []
        async for d in cursor:
            serialized = self._serialize_device(d)
            if serialized:
                devices.append(serialized)

        return devices


    async def list_devices(self):
        cursor = self.repo.list_all()

        devices = []
        async for d in cursor:
            serialized = self._serialize_device(d)
            if serialized:
                devices.append(serialized)

        return devices