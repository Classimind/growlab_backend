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
    FarmRole.VIEWER: [
        "read_farm"
    ],

    FarmRole.STAFF: [
        "read_farm",
        "write_farm"
    ],

    FarmRole.MANAGER: [
        "read_farm",
        "write_farm",
        "manage_tasks"
    ],

    FarmRole.ADMIN: [
        "read_farm",
        "write_farm",
        "manage_users",
        "manage_farm"
    ],

    FarmRole.OWNER: [
        "all"
    ]
}