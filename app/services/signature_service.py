import base64
from pathlib import Path

from app.utils.directories import sha256_file
from app.core.signer import sign_data, verify_signature


class SignatureService:

    @staticmethod
    def sign_file(file_path: Path) -> bytes:
        digest = sha256_file(file_path)
        return sign_data(digest.encode())

    @staticmethod
    def save_signature(path: Path, signature: bytes):
        path.write_bytes(signature)

    @staticmethod
    def encode_signature(signature: bytes) -> str:
        return base64.b64encode(signature).decode("ascii")

    @staticmethod
    def verify_signature(file_path: Path, signature: bytes) -> bool:
        expected = sha256_file(file_path)
        # optional: verify via public key (not implemented here yet)
        return bool(signature) and len(expected) == 64