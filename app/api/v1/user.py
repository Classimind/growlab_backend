from fastapi import APIRouter,HTTPException,status
from app.models.user import Token,EmailSignup,Provider,OAuthLogin, FCMTokenUpdate, User
from app.services.token_service import generate_tokens,decode_token,create_access_token,get_current_user
from app.services.user_service import UserService
from pymongo.errors import DuplicateKeyError
from fastapi import APIRouter, Depends, HTTPException
from app.models.user import RefreshRequest,UserProfile
from fastapi.security import OAuth2PasswordRequestForm
router = APIRouter()

def get_user_service():
    return UserService()



@router.post("/refresh")
async def refresh_token(data: RefreshRequest):
    payload = decode_token(data.refresh_token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("user_id")
    email = payload.get("email")
    role = payload.get("role")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    #  create new access token
    new_access_token,expire = create_access_token({
        "user_id": user_id,
        "role": role,
        "email":email
    })

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        'expire':expire.strftime("%Y-%m-%d %H:%M:%S")
    }


@router.post("/signup", response_model=Token)
async def signup(
    data: EmailSignup,
    user_service: UserService = Depends(get_user_service)
):
    try:
        user = await user_service.add_user({
            "email": data.email,
            "password": data.password,
            "provider": Provider.EMAIL
        })

    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Email already registered")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error {e}")

    payload = {
        "_id": str(user["_id"]),
        "email": user["email"],
        "role": user["role"].value if hasattr(user["role"], "value") else str(user["role"])
    }
    return generate_tokens(payload)

@router.post("/login", response_model=Token)
async def login(
    data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service)
):
    try:
        print(data)
        user = await user_service.authenticate_email_user(
            data.username,
            data.password
        )

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # normalize role safely
        role = user["role"].value if hasattr(user["role"], "value") else str(user["role"])

        payload = {
            "_id": str(user["_id"]),   
            "email": str(user["email"]),
            "role": role
        }

        return generate_tokens(payload)

    except HTTPException as http_exc:
        raise http_exc
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/", response_model=User)
async def get_user_by_id(
    user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    user = await user_service.get_user_by_id(user["user_id"])
    if not user:
        raise HTTPException(404, "User not found")

    return user

@router.patch(
    "/update/profile",
    response_model=User,
    status_code=status.HTTP_200_OK
)
async def update_user_profile(
    payload: UserProfile,
    user=Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):

    update_data = payload.model_dump(exclude_unset=True)
    user = await user_service.update_user_profile(user["user_id"], update_data)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user 



@router.put("/fcm-token")
async def update_fcm_token(
    data: FCMTokenUpdate,
    user=Depends(get_current_user),
    user_service=Depends(get_user_service),
):
    try:
        token = data.fcm_token.strip()

        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="FCM token cannot be empty"
            )

        updated = await user_service.update_fcm_token(
            user_id=user['user_id'],
            token=token
        )

        if not updated:
            return {
                "success": True,
                "message": "FCM token already up to date"
            }

        return {
            "success": True,
            "message": "FCM token updated successfully"
        }

    except HTTPException:
        raise

    except Exception as e:
        print(f"FCM update error: {e}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update FCM token"
        )
    
@router.post("/oauth-login", response_model=Token)
async def oauth_login(data: OAuthLogin,user_service: UserService = Depends(get_user_service)):
    
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
