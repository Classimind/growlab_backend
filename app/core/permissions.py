from app.core.roles import Role,FarmRole


ROLE_PERMISSIONS = {
    Role.USER: ["read_profile"],

    Role.RESEARCHER: [
        "read_profile",
        "analyze_data"
    ],

    Role.ADMIN: [
        "read_profile",
        "manage_users",
        "system_write"
    ],

    Role.SUPER_ADMIN: [
        "all"
    ]
}



FARM_ROLE_PERMISSIONS = {
    FarmRole.OWNER: [
        "read", "create", "update", "delete", "manage_farm", "manage_users"
    ],

    FarmRole.ADMIN: [
        "read", "create", "update", "delete", "manage_users"
    ],

    FarmRole.MANAGER: [
        "read", "create", "update", "manage_sensors"
    ],

    FarmRole.STAFF: [
        "read", "create"
    ],

    FarmRole.VIEWER: [
        "read"
    ]
}