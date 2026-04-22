from enum import Enum

class Role(str, Enum):
    USER = "user"
    RESEARCHER = "researcher"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class FarmRole(str, Enum):
    VIEWER = "viewer"
    STAFF = "staff"
    MANAGER = "manager"
    ADMIN = "admin"
    OWNER = "owner"