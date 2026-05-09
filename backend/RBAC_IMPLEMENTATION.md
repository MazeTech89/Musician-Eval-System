# RBAC Implementation Guide

## Overview

A complete Role-Based Access Control (RBAC) system has been implemented for the Musician Evaluation System backend using FastAPI, SQLAlchemy, and JWT authentication with RS256 asymmetric cryptography.

## Architecture

### 1. Database Models

**Location:** `backend/app/models/user.py`

- **User**: Stores user account information with role assignment
- **Role**: Defines available roles (Admin, Evaluator, Musician, Moderator, Analyst)
- **Permission**: Granular permissions assignable to roles
- **Enums**: `RoleEnum` and `PermissionEnum` for type safety

### 2. Roles and Permissions

#### Roles

| Role | Description | Use Case |
|------|-------------|----------|
| **Admin** | Full system access | System administrators |
| **Evaluator** | Submit evaluations, view performances | Judges/Teachers |
| **Musician** | Submit performances, view own evaluations | Students/Performers |
| **Moderator** | Review evaluation consistency | Quality assurance |
| **Analyst** | Read-only access to reports | Data analysts |

#### Permission Matrix

```
┌─────────────────────┬───────┬────────────┬──────────┬────────────┬────────┐
│ Resource            │ Admin │ Evaluator  │ Musician │ Moderator  │Analyst │
├─────────────────────┼───────┼────────────┼──────────┼────────────┼────────┤
│ Users               │ CRUD* │ R (self)   │ R (self) │ R          │ -      │
│ Performances        │ R     │ R (all)    │ CU (own) │ R (all)    │ R      │
│ Evaluations         │ RUD   │ CU (own)   │ R (own)  │ R (all)    │ R      │
│ Settings            │ CUD   │ -          │ -        │ -          │ -      │
│ Reports             │ R     │ R (own)    │ R (own)  │ R+Export   │ R+Exp  │
│ Audit Logs          │ R     │ -          │ -        │ -          │ -      │
└─────────────────────┴───────┴────────────┴──────────┴────────────┴────────┘
*C=Create, U=Update, D=Delete, R=Read
```

### 3. Security

**Location:** `backend/app/core/security.py`

- **Password Hashing**: Argon2id (resistant to GPU/ASIC attacks)
- **JWT Tokens**: RS256 asymmetric cryptography (default: HS256 for development)
- **Token Expiration**: Configurable (default: 30 minutes)

### 4. Authentication Endpoints

**Base URL:** `/api/v1/auth`

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/register` | POST | None | Register new user |
| `/login` | POST | None | Authenticate user |
| `/me` | GET | Required | Get current user info |
| `/me` | PUT | Required | Update current user |
| `/change-password` | POST | Required | Change password |
| `/users` | GET | Admin | List all users |
| `/users/{id}` | GET | Admin | Get user by ID |
| `/users/{id}` | PUT | Admin | Update user |
| `/users/{id}` | DELETE | Admin | Delete user (soft) |

### 5. Request/Response Examples

#### Registration
```bash
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "role": "musician"
}
```

#### Login
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "SecurePass123!"
}

Response:
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### Protected Request
```bash
GET /api/v1/auth/me
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Implementation Details

### File Structure

```
backend/
├── app/
│   ├── api/v1/
│   │   ├── auth.py          # Auth endpoints
│   │   └── __init__.py      # Include auth router
│   ├── core/
│   │   ├── security.py      # JWT & password utilities
│   │   ├── database.py      # Database configuration
│   │   ├── dependencies.py  # FastAPI dependencies
│   │   ├── init_db.py       # DB initialization
│   │   └── config.py        # Updated with RS256 support
│   ├── models/
│   │   └── user.py          # User, Role, Permission models
│   ├── schemas/
│   │   └── auth.py          # Pydantic schemas
│   ├── services/
│   │   └── auth.py          # Business logic
│   └── main.py              # Updated with DB initialization
└── tests/unit/
    └── test_auth.py         # Comprehensive auth tests
```

### Using Role-Based Dependencies

```python
from fastapi import APIRouter, Depends
from app.core.dependencies import (
    get_current_active_user,
    get_current_admin,
    require_role,
    require_permission,
)
from app.models.user import RoleEnum, PermissionEnum

router = APIRouter()

# Admin-only endpoint
@router.get("/admin-only")
async def admin_endpoint(user = Depends(get_current_admin)):
    return {"message": "Admin access granted"}

# Specific role requirement
@router.post("/evaluations")
async def submit_evaluation(
    user = Depends(require_role(RoleEnum.EVALUATOR, RoleEnum.ADMIN))
):
    return {"message": "Evaluation submitted"}

# Permission-based requirement
@router.get("/reports")
async def get_reports(
    user = Depends(require_permission(PermissionEnum.REPORT_READ))
):
    return {"data": "reports"}
```

### Service Layer Example

```python
from app.services.auth import AuthService, RoleService
from app.core.database import get_db
from sqlalchemy.orm import Session

def get_user_by_id(user_id: int, db: Session):
    user = AuthService.get_user_by_id(db, user_id)
    if user:
        permissions = RoleService.get_user_permissions(db, user)
        return {
            "user": user,
            "permissions": permissions
        }
    return None
```

## Setup and Configuration

### 1. Update Environment Variables

Create/update `.env` file:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/musician_eval

# Security
SECRET_KEY=your-secret-key-generate-new-one-in-production
ALGORITHM=RS256

# For RS256 (optional, leave empty for default HS256 in dev)
RSA_PRIVATE_KEY=""
RSA_PUBLIC_KEY=""

# Access Token
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 2. Initialize Database

```bash
cd backend
python -m app.core.init_db
```

This will:
- Create all database tables
- Create default roles
- Create all permissions
- Assign permissions to roles

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Key packages:
- `fastapi==0.115.0` - Web framework
- `sqlalchemy==2.0.35` - ORM
- `alembic==1.13.3` - Database migrations
- `psycopg[binary]==3.3.4` - PostgreSQL driver
- `python-jose[cryptography]==3.3.0` - JWT
- `argon2-cffi==23.1.0` - Password hashing

### 4. Run Development Server

```bash
uvicorn app.main:app --reload
```

## Testing

Run authentication tests:

```bash
pytest tests/unit/test_auth.py -v
```

Test coverage includes:
- User registration and validation
- Login and token generation
- Password hashing and verification
- Role-based access control
- Permission checking
- User management (admin)
- Password change functionality

## Migration Path

To add RBAC to existing endpoints:

1. **Import Dependencies**
   ```python
   from app.core.dependencies import get_current_active_user, require_role
   from app.models.user import RoleEnum
   ```

2. **Add Authentication**
   ```python
   @router.get("/endpoint")
   async def my_endpoint(user = Depends(get_current_active_user)):
       # User is authenticated
       pass
   ```

3. **Add Authorization**
   ```python
   @router.delete("/endpoint")
   async def delete_endpoint(user = Depends(require_role(RoleEnum.ADMIN))):
       # Only admins can access
       pass
   ```

## Security Best Practices

✅ **Implemented:**
- Argon2id password hashing
- RS256 asymmetric JWT tokens (configured)
- HTTP Bearer token authentication
- Role and permission-based access control
- Soft delete for users (deactivation)
- Last login tracking
- CORS configuration
- SQL injection prevention (SQLAlchemy ORM)

⚠️ **Production Recommendations:**
- Use RSA keys (RSA_PRIVATE_KEY, RSA_PUBLIC_KEY)
- Rotate SECRET_KEY regularly
- Use HTTPS only
- Implement rate limiting
- Add audit logging
- Enable database SSL
- Use environment-specific configuration
- Implement token refresh mechanism
- Add 2FA/MFA support

## Troubleshooting

### Import Errors

If you get import errors about missing modules:
```bash
pip install -r requirements.txt
python -m app.core.init_db
```

### Database Connection Issues

Check `.env` DATABASE_URL format:
```
postgresql://username:password@hostname:5432/database_name
```

### JWT Token Errors

Verify token format: `Authorization: Bearer <token>`

### Role Not Found Errors

Run database initialization:
```bash
python -m app.core.init_db
```

## Next Steps

1. **Extend Permissions**: Add more granular permissions as needed
2. **Add Audit Logging**: Track all user actions
3. **Implement Refresh Tokens**: For better token management
4. **Add 2FA**: For enhanced security
5. **Create Admin Dashboard**: For user management
6. **Add Resource-Level Permissions**: For finer control

## References

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [OWASP ASVS L2](https://owasp.org/www-project-application-security-verification-standard/)
- [Argon2 Password Hashing](https://github.com/hynek/argon2-cffi)
