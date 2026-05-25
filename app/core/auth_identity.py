from fastapi import Depends, Header, HTTPException
from jose import JWTError
from fastapi.security import APIKeyHeader
from app.services.api_key_service import APIKeyService
from app.db.clients import get_db
from fastapi.security import OAuth2PasswordBearer
from app.services.token_service import decode_token



api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login",auto_error=False)

async def get_current_user(
    api_key: str | None = Depends(api_key_header),
    token: str | None = Depends(oauth2_scheme),
    db=Depends(get_db)
):
    user_id = None
    role = None
    api_key_doc = None

    if token:
        try:
            payload = decode_token(token)

            user_id = payload.get("user_id")
            role = payload.get("role")

            if not user_id:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token"
                )

        except JWTError:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    if api_key:
        service = APIKeyService(db)
        api_key_doc = await service.validate_api(api_key)

        if not api_key_doc:
            raise HTTPException(
                status_code=403,
                detail="Invalid API key"
            )

    if not user_id and not api_key_doc:
        raise HTTPException(
            status_code=401,
            detail="No authentication provided"
        )

    if user_id and api_key_doc:
        if str(api_key_doc["user_id"]) != str(user_id):
            raise HTTPException(
                status_code=403,
                detail="API key does not belong to this user"
            )

    if not user_id and api_key_doc:
        user_id = api_key_doc["user_id"]

    return {
        "user_id": str(user_id),
        "role": role,
        "api_key": api_key_doc,
        "lab_id": api_key_doc["lab_id"] if api_key_doc else None,
        "permissions": api_key_doc["permissions"] if api_key_doc else [],
        "auth_type": (
            "dual" if user_id and api_key_doc else
            "api_key" if api_key_doc else
            "jwt"
        )
    }
