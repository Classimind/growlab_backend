import re
from fastapi import HTTPException

DEVICE_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


def validate_device(device: str):
    if not DEVICE_RE.match(device):
        raise HTTPException(status_code=400, detail="Invalid device name")


def safe_filename(filename: str) -> str:
    return filename.split("/")[-1].split("\\")[-1]