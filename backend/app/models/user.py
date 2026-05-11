"""User and role models for database."""

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class RoleEnum(str, Enum):
    """Available roles in the system."""

    ADMIN = "admin"
    EVALUATOR = "evaluator"
    MUSICIAN = "musician"
    MODERATOR = "moderator"
    ANALYST = "analyst"


class PermissionEnum(str, Enum):
    """Available permissions in the system."""

    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # Performance management
    PERFORMANCE_CREATE = "performance:create"
    PERFORMANCE_READ = "performance:read"
    PERFORMANCE_UPDATE = "performance:update"
    PERFORMANCE_DELETE = "performance:delete"

    # Evaluation management
    EVALUATION_CREATE = "evaluation:create"
    EVALUATION_READ = "evaluation:read"
    EVALUATION_UPDATE = "evaluation:update"
    EVALUATION_DELETE = "evaluation:delete"

    # System settings
    SETTINGS_READ = "settings:read"
    SETTINGS_UPDATE = "settings:update"

    # Reports
    REPORT_READ = "report:read"
    REPORT_EXPORT = "report:export"

    # Audit logs
    AUDIT_READ = "audit:read"


# Association table for Role-Permission many-to-many relationship
role_permission_association = Table(
    "role_permission",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("role.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permission.id"), primary_key=True),
)


class Role(Base):
    """Role model for RBAC."""

    __tablename__ = "role"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(SQLEnum(RoleEnum), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    users = relationship("User", back_populates="role")
    permissions = relationship(
        "Permission", secondary=role_permission_association, back_populates="roles"
    )

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class Permission(Base):
    """Permission model for RBAC."""

    __tablename__ = "permission"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(SQLEnum(PermissionEnum), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    roles = relationship(
        "Role", secondary=role_permission_association, back_populates="permissions"
    )

    def __repr__(self) -> str:
        return f"<Permission {self.name}>"


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("role.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    role = relationship("Role", back_populates="users")
    performances = relationship(
        "Performance", back_populates="musician", foreign_keys="Performance.musician_id"
    )
    evaluations = relationship(
        "Evaluation", back_populates="evaluator", foreign_keys="Evaluation.evaluator_id"
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"
