from fastapi import Depends, HTTPException
from app.core.permissions import ROLE_PERMISSIONS,FARM_ROLE_PERMISSIONS
from app.core.roles import Role,FarmRole
from app.services.token_service import get_current_user

def require_permission(permission: str):

    def checker(user=Depends(get_current_user)):

        role = user.get("role")

        # normalize role (IMPORTANT for JWT safety)
        role = Role(role)

        # SUPER ADMIN bypass
        if role == Role.SUPER_ADMIN:
            return user

        permissions = ROLE_PERMISSIONS.get(role, [])

        if permission not in permissions:
            raise HTTPException(status_code=403, detail="Permission denied")

        return user

    return checker



def require_farm_permission(farm_id: str, permission: str):

    def checker(user=Depends(get_current_user)):

        # global override
        role = Role(user.get("role"))
        if role == Role.SUPER_ADMIN:
            return user

        # get farm role
        farm_role = user.get("domain_ids", {}).get(farm_id)

        if not farm_role:
            raise HTTPException(403, "No access to this farm")

        farm_role = FarmRole(farm_role)

        permissions = FARM_ROLE_PERMISSIONS.get(farm_role, [])

        if permission not in permissions:
            raise HTTPException(403, "Permission denied")

        return user

    return checker