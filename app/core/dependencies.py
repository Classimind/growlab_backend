from fastapi import Depends, HTTPException
from app.core.permissions import ROLE_PERMISSIONS,FARM_ROLE_PERMISSIONS
from app.core.roles import Role,FarmRole
from app.services.token_service import get_current_user
from app.models.farm import Lab

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


def require_roles(allowed_roles: list):
    def dependency(user=Depends(get_current_user)):
        
        if user['role'] not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Permission denied"
            )
        return user
    return dependency

def can_access_farm(user, lab, action: str = "read") -> bool:
    user_id = str(user["user_id"])
    print(user_id)
    if isinstance(lab, dict):
        created_by = str(lab.get("created_by"))

        employees = lab.get("employees", [])
    else:
        created_by = str(lab.created_by)
        employees = lab.employees or []

    if created_by == user_id:
        return action in FARM_ROLE_PERMISSIONS[FarmRole.OWNER]
    for emp in employees:

        if isinstance(emp, dict):
            emp_user_id = str(emp.get("user_id"))
            role = emp.get("role")
            permissions = emp.get("permissions")

        else:
            emp_user_id = str(emp.user_id)
            role = emp.role
            permissions = emp.permissions

        if emp_user_id == user_id:

            if permissions:
                return action in permissions

            return action in FARM_ROLE_PERMISSIONS.get(role, [])

    return False


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