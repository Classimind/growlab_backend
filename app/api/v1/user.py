from fastapi import APIRouter,HTTPException
from app.models.user import Token,EmailSignup,EmailLogin,Provider,OAuthLogin
from app.services.token_service import create_access_token,decode_token,create_refresh_token
from app.services.user_service import UserService
from pymongo.errors import DuplicateKeyError
router = APIRouter()


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    payload = decode_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    email = payload.get("sub")
    access_token = create_access_token({"sub": email})
    return {"access_token": access_token}

@router.post("/signup", response_model=Token)
async def signup(data: EmailSignup):
    user_service = UserService()
    try:
        user =await  user_service.add_user({
            "email": data.email,
            "password": data.password,  
            "provider": Provider.EMAIL
        })
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Email already registered")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Fallback for any unexpected DB errors
        raise HTTPException(status_code=500, detail=f"Internal server error {e}")

    access_token = create_access_token({"sub": user["email"]})
    refresh_token = create_refresh_token({"sub": user["email"]})
    return {"access_token": access_token,"refresh_token":refresh_token}

@router.post("/login", response_model=Token)
async def login(data: EmailLogin):
    user_service= UserService()
    user = await user_service.authenticate_email_user(data.email, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": user["email"]})
    refresh_token = create_refresh_token({"sub": user["email"]})
    return {"access_token": access_token,"refresh_token":refresh_token}

@router.post("/oauth-login", response_model=Token)
async def oauth_login(data: OAuthLogin):
    user_service= UserService()
    # Check if user exists
    user = await user_service.find_user_by_provider_id(data.provider, data.provider_user_id)

    if not user:
        # Create new OAuth user
        user_data = {
            "provider": data.provider,
            "oauth": {
                "provider": data.provider,
                "provider_user_id": data.provider_user_id,
                "email": data.email,
                "name": data.name,
                "avatar_url": data.avatar_url,
                "access_token": data.access_token
            }
        }
        user = user_service.add_user(user_data)
        
    access_token = create_access_token({"sub": f"{data.provider}:{data.provider_user_id}"})
    refresh_token = refresh_token({"sub": f"{data.provider}:{data.provider_user_id}"})
    return {"access_token": access_token,"refresh_token":refresh_token}
