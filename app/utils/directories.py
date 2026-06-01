import hashlib
from pathlib import Path


BASE_DIR = Path("firmwares")


def get_device_dir(device: str) -> Path:
    path = BASE_DIR / device
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_latest_version(device: str) -> int:
    firmware_dir = BASE_DIR / device / "firmware"
    print(f"Looking for firmware in {firmware_dir}")
    if not firmware_dir.exists():
        return 0

    versions = [
        int(f.stem.replace("v", ""))
        for f in firmware_dir.glob("v*.bin")
    ]
    print(f"Found firmware versions for {device}: {versions}")

    return max(versions, default=0)


def sha256_file(path: Path) -> str:
    sha = hashlib.sha256()

    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            sha.update(chunk)

    return sha.hexdigest()