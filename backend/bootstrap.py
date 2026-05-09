"""Bootstrap script to initialize database with default admin user."""

import sys

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.init_db import init_database
from app.core.security import hash_password
from app.models.user import Role, RoleEnum, User


def create_admin_user(db: Session, username: str, email: str, password: str) -> bool:
    """Create an admin user.

    Args:
        db: Database session
        username: Admin username
        email: Admin email
        password: Admin password

    Returns:
        True if successful, False otherwise
    """
    # Check if user already exists
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        print(f"✗ User '{username}' already exists")
        return False

    # Get admin role
    admin_role = db.query(Role).filter(Role.name == RoleEnum.ADMIN).first()
    if not admin_role:
        print("✗ Admin role not found. Run init_db first.")
        return False

    # Create admin user
    admin_user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        first_name="Admin",
        last_name="User",
        role_id=admin_role.id,
        is_active=True,
    )

    db.add(admin_user)
    db.commit()

    print(f"✓ Admin user '{username}' created successfully")
    print(f"  Email: {email}")
    print("  Role: admin")
    return True


def main():
    """Initialize database and create admin user."""
    print("=" * 60)
    print("MUSICIAN EVALUATION SYSTEM - DATABASE BOOTSTRAP")
    print("=" * 60)
    print()

    # Initialize database
    print("Step 1: Initializing database...")
    try:
        init_database()
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        sys.exit(1)

    print()
    print("Step 2: Creating admin user...")

    # Get credentials from input or use defaults
    print()
    print("Please provide admin user credentials:")

    username = input("Admin username [admin]: ").strip() or "admin"
    email = input("Admin email [admin@example.com]: ").strip() or "admin@example.com"

    # Get password
    import getpass

    password = getpass.getpass("Admin password: ").strip()

    if not password:
        print("✗ Password is required")
        sys.exit(1)

    # Create admin user
    db = SessionLocal()
    try:
        if not create_admin_user(db, username, email, password):
            print("✗ Failed to create admin user")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Error creating admin user: {e}")
        sys.exit(1)
    finally:
        db.close()

    print()
    print("=" * 60)
    print("✓ DATABASE BOOTSTRAP COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print()
    print("You can now login with:")
    print(f"  Username: {username}")
    print(f"  Email: {email}")
    print()
    print("Next steps:")
    print("1. Start the server: uvicorn app.main:app --reload")
    print("2. Login at: POST /api/v1/auth/login")
    print("3. Register new users at: POST /api/v1/auth/register")
    print()


if __name__ == "__main__":
    main()
