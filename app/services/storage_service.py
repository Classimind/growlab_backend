import os
import json
import uuid
import hashlib
from pathlib import Path


class ResumableStorage:

    BASE = Path("storage")


    @staticmethod
    def create_upload_session(device: str, version: int, expected_size: int):
        session_id = str(uuid.uuid4())

        session_dir = ResumableStorage.BASE / device / "sessions" / session_id
        chunk_dir = session_dir / "chunks"

        chunk_dir.mkdir(parents=True, exist_ok=True)

        meta = {
            "session_id": session_id,
            "device": device,
            "version": version,
            "offset": 0,
            "expected_size": expected_size,
            "status": "uploading",
            "sha256": hashlib.sha256().hexdigest(),
        }

        (session_dir / "meta.json").write_text(json.dumps(meta))

        return meta


    @staticmethod
    def get_session(device: str, session_id: str):
        path = ResumableStorage.BASE / device / "sessions" / session_id / "meta.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    @staticmethod
    def update_offset(device: str, session_id: str, offset: int):
        path = ResumableStorage.BASE / device / "sessions" / session_id / "meta.json"
        meta = json.loads(path.read_text())
        meta["offset"] = offset
        path.write_text(json.dumps(meta))


    @staticmethod
    def write_chunk(device: str, session_id: str, chunk_index: int, data: bytes):
        chunk_file = (
            ResumableStorage.BASE
            / device
            / "sessions"
            / session_id
            / "chunks"
            / f"{chunk_index}.part"
        )

        chunk_file.write_bytes(data)
        return chunk_file