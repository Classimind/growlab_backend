from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

# Load environment variables
load_dotenv()

# -------------------------
# JWT Config
# -------------------------
SECRET_KEY = os.getenv("TOKEN_SECRET_KEY", "your-default-secret")  # fallback secret
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60        # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS = 30          # 30 days


# "Take token from Authorization: Bearer <token>"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    print(token)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token) 
        user_id: str = payload.get("user_id")
        role: str = payload.get("role")

        if user_id is None:
            raise credentials_exception

        return {
            "user_id": user_id,
            "role": role
        }

    except JWTError:
        raise credentials_exception



def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> tuple:
    """
    Create a JWT access token with optional expiration.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM),expire


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token with optional expiration.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)



# def get_current_user(token: str = Depends()):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Invalid or expired token",
#         headers={"WWW-Authenticate": "Bearer"},
#     )

#     try:
#         payload = decode_token(token)
#         user_id: str = payload.get("sub")
#         role: str = payload.get("role")

#         if user_id is None:
#             raise credentials_exception

#         return {
#             "user_id": user_id,
#             "role": role
#         }

#     except JWTError:
#         raise credentials_exception



# -------------------------
# Token Decoding Function
# -------------------------

def decode_token(token: str) -> Optional[dict]:
    """
    Decode a JWT token (access or refresh). Returns payload if valid, None if invalid/expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_tokens( user: dict):
        payload = {
            "user_id": str(user["_id"]),
            "email": user["email"],
            "role": user["role"] 
        }
        access_token,expire= create_access_token(payload)
        return {
            "access_token": access_token,
            "refresh_token": create_refresh_token(payload),
            "token_type": "bearer",
            "expire":expire.strftime("%Y-%m-%d %H:%M:%S")
        }


