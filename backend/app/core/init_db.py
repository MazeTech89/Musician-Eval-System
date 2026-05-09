"""Database initialization script with default roles and permissions."""

from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine
from app.models.user import Base, Permission, PermissionEnum, Role, RoleEnum


def init_roles_and_permissions(db: Session) -> None:
    """Initialize default roles and permissions.

    Args:
        db: Database session
    """
    # Define role descriptions
    role_descriptions = {
        RoleEnum.ADMIN: "Administrator with full system access",
        RoleEnum.EVALUATOR: "Evaluator who can submit performance evaluations",
        RoleEnum.MUSICIAN: "Musician who can submit performances for evaluation",
        RoleEnum.MODERATOR: "Moderator who reviews evaluations for consistency",
        RoleEnum.ANALYST: "Analyst with read-only access to reports and analytics",
    }

    # Define permissions per role
    role_permissions = {
        RoleEnum.ADMIN: [
            PermissionEnum.USER_CREATE,
            PermissionEnum.USER_READ,
            PermissionEnum.USER_UPDATE,
            PermissionEnum.USER_DELETE,
            PermissionEnum.PERFORMANCE_CREATE,
            PermissionEnum.PERFORMANCE_READ,
            PermissionEnum.PERFORMANCE_UPDATE,
            PermissionEnum.PERFORMANCE_DELETE,
            PermissionEnum.EVALUATION_CREATE,
            PermissionEnum.EVALUATION_READ,
            PermissionEnum.EVALUATION_UPDATE,
            PermissionEnum.EVALUATION_DELETE,
            PermissionEnum.SETTINGS_READ,
            PermissionEnum.SETTINGS_UPDATE,
            PermissionEnum.REPORT_READ,
            PermissionEnum.REPORT_EXPORT,
            PermissionEnum.AUDIT_READ,
        ],
        RoleEnum.EVALUATOR: [
            PermissionEnum.PERFORMANCE_READ,
            PermissionEnum.EVALUATION_CREATE,
            PermissionEnum.EVALUATION_READ,
            PermissionEnum.EVALUATION_UPDATE,
            PermissionEnum.REPORT_READ,
        ],
        RoleEnum.MUSICIAN: [
            PermissionEnum.PERFORMANCE_CREATE,
            PermissionEnum.PERFORMANCE_READ,
            PermissionEnum.PERFORMANCE_UPDATE,
            PermissionEnum.EVALUATION_READ,
        ],
        RoleEnum.MODERATOR: [
            PermissionEnum.PERFORMANCE_READ,
            PermissionEnum.EVALUATION_READ,
            PermissionEnum.REPORT_READ,
            PermissionEnum.REPORT_EXPORT,
        ],
        RoleEnum.ANALYST: [
            PermissionEnum.REPORT_READ,
            PermissionEnum.REPORT_EXPORT,
        ],
    }

    # Create permissions if they don't exist
    permission_map = {}
    for perm_enum in PermissionEnum:
        existing = db.query(Permission).filter(Permission.name == perm_enum).first()
        if not existing:
            perm = Permission(
                name=perm_enum,
                description=f"Permission to {perm_enum.value}",
            )
            db.add(perm)
            db.flush()
            permission_map[perm_enum] = perm
        else:
            permission_map[perm_enum] = existing

    # Create roles with permissions if they don't exist
    for role_enum, perms in role_permissions.items():
        existing_role = db.query(Role).filter(Role.name == role_enum).first()
        if not existing_role:
            role = Role(
                name=role_enum,
                description=role_descriptions[role_enum],
            )
            # Add permissions to role
            for perm_enum in perms:
                role.permissions.append(permission_map[perm_enum])
            db.add(role)
        else:
            # Update permissions for existing role
            existing_role.permissions.clear()
            for perm_enum in perms:
                existing_role.permissions.append(permission_map[perm_enum])

    db.commit()
    print("✓ Roles and permissions initialized successfully")


def init_database() -> None:
    """Initialize the database with all tables and default data."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")

    # Initialize roles and permissions
    db = SessionLocal()
    try:
        init_roles_and_permissions(db)
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
    print("✓ Database initialization completed")
