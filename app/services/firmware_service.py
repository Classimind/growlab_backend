import json
import uuid
from pathlib import Path
from typing import Dict, List

from app.core.config import settings
from app.utils.directories import sha256_file


class FirmwareService:
    """
    OTA Firmware Service:
    - resumable upload sessions
    - versioned firmware storage
    - chunk-based assembly
    """

    BASE = Path(settings.FIRMWARE_ROOT)

    # ---------------- INIT SESSION ----------------
    @staticmethod
    async def init_upload_session(device: str, file_size: int) -> Dict:
        session_id = str(uuid.uuid4())

        session_dir = FirmwareService.BASE / device / "sessions" / session_id
        chunk_dir = session_dir / "chunks"

        chunk_dir.mkdir(parents=True, exist_ok=True)

        meta = {
            "session_id": session_id,
            "device": device,
            "file_size": file_size,
            "offset": 0,
            "status": "uploading",
        }

        (session_dir / "meta.json").write_text(json.dumps(meta))

        return meta

    # ---------------- WRITE CHUNK ----------------
    @staticmethod
    async def write_chunk(device: str, session_id: str, chunk_index: int, data: bytes):
        session_dir = FirmwareService.BASE / device / "sessions" / session_id

        meta_path = session_dir / "meta.json"
        if not meta_path.exists():
            raise ValueError("Invalid session")

        chunk_file = session_dir / "chunks" / f"{chunk_index}.part"
        chunk_file.write_bytes(data)

        meta = json.loads(meta_path.read_text())
        meta["offset"] += len(data)

        meta_path.write_text(json.dumps(meta))

        return {
            "session_id": session_id,
            "offset": meta["offset"],
        }

    # ---------------- FINALIZE UPLOAD ----------------
    @staticmethod
    async def finalize_upload(device: str, session_id: str):

        session_dir = FirmwareService.BASE / device / "sessions" / session_id
        chunks_dir = session_dir / "chunks"

        meta_path = session_dir / "meta.json"
        meta = json.loads(meta_path.read_text())

        version = FirmwareService.get_next_version(device)

        final_path = FirmwareService.BASE / device / "firmware" / f"v{version}.bin"
        final_path.parent.mkdir(parents=True, exist_ok=True)

        sha = sha256_file(final_path) if final_path.exists() else ""

        import hashlib
        hasher = hashlib.sha256()

        with open(final_path, "wb") as out:
            for chunk in sorted(chunks_dir.iterdir()):
                data = chunk.read_bytes()
                out.write(data)
                hasher.update(data)

        meta.update({
            "version": version,
            "status": "completed",
            "sha256": hasher.hexdigest(),
        })

        meta_path.write_text(json.dumps(meta))

        return meta

    # ---------------- VERSIONING ----------------
    @staticmethod
    def get_next_version(device: str) -> int:
        device_dir = FirmwareService.BASE / device / "firmware"
        device_dir.mkdir(parents=True, exist_ok=True)

        versions = [
            int(p.stem.replace("v", ""))
            for p in device_dir.glob("v*.bin")
        ]

        return max(versions, default=0) + 1

    # ---------------- FILE ACCESS ----------------
    @staticmethod
    def get_file(device: str, filename: str) -> Path:
        return FirmwareService.BASE / device / "firmware" / filename

    # ---------------- LIST FILES ----------------
    @staticmethod
    async def list_files(device: str) -> List[dict]:
        device_dir = FirmwareService.BASE / device / "firmware"

        if not device_dir.exists():
            return []

        return [
            {
                "name": f.name,
                "size": f.stat().st_size,
            }
            for f in device_dir.glob("v*.bin")
        ]