"""
User, Role, and Permission models for authentication and authorization
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, 
    Table, UniqueConstraint, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from passlib.context import CryptContext

from .base import Base

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Association tables
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('assigned_at', DateTime(timezone=True), server_default='now()', nullable=False),
    Column('expires_at', DateTime(timezone=True), nullable=True),
    UniqueConstraint('user_id', 'role_id', name='uq_user_role')
)

role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
    UniqueConstraint('role_id', 'permission_id', name='uq_role_permission')
)


class User(Base):
    """User model with authentication and soft delete support"""
    
    __tablename__ = 'users'
    
    # Columns
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    preferences = Column(JSON, default=dict)
    last_login = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    roles = relationship(
        'Role',
        secondary=user_roles,
        back_populates='users',
        lazy='selectin'
    )
    conversations = relationship('Conversation', back_populates='owner', cascade='all, delete-orphan')
    audit_logs = relationship('AuditLog', back_populates='user', cascade='all, delete-orphan')
    export_jobs = relationship('ExportJob', back_populates='user', cascade='all, delete-orphan')
    bookmarks = relationship('Bookmark', back_populates='user', cascade='all, delete-orphan')
    annotations = relationship('Annotation', back_populates='user', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        Index('idx_users_active', 'is_active', 'deleted_at'),
        Index('idx_users_email_active', 'email', postgresql_where='deleted_at IS NULL'),
    )
    
    def set_password(self, password: str) -> None:
        """Hash and set password"""
        self.password_hash = pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(password, self.password_hash)
    
    def has_permission(self, resource: str, action: str) -> bool:
        """Check if user has specific permission"""
        for role in self.roles:
            for permission in role.permissions:
                if permission.resource == resource and permission.action == action:
                    return True
        return False
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has specific role"""
        return any(role.name == role_name for role in self.roles)
    
    def get_permissions(self) -> List[str]:
        """Get all user permissions as list of strings"""
        permissions = []
        for role in self.roles:
            for permission in role.permissions:
                permissions.append(f"{permission.resource}:{permission.action}")
        return list(set(permissions))  # Remove duplicates
    
    @property
    def is_deleted(self) -> bool:
        """Check if user is soft deleted"""
        return self.deleted_at is not None


class Role(Base):
    """Role model for RBAC"""
    
    __tablename__ = 'roles'
    
    # Columns
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    
    # Relationships
    users = relationship(
        'User',
        secondary=user_roles,
        back_populates='roles'
    )
    permissions = relationship(
        'Permission',
        secondary=role_permissions,
        back_populates='roles',
        lazy='selectin'
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_roles_name', 'name'),
    )


class Permission(Base):
    """Permission model for fine-grained access control"""
    
    __tablename__ = 'permissions'
    
    # Columns
    resource = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)
    description = Column(String(255), nullable=True)
    
    # Relationships
    roles = relationship(
        'Role',
        secondary=role_permissions,
        back_populates='permissions'
    )
    
    # Indexes
    __table_args__ = (
        UniqueConstraint('resource', 'action', name='uq_resource_action'),
        Index('idx_permissions_resource', 'resource'),
    )
    
    def __str__(self) -> str:
        """String representation"""
        return f"{self.resource}:{self.action}"


class UserRole(Base):
    """User-Role association with additional fields"""
    
    __tablename__ = 'user_role_details'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id'), nullable=False)
    assigned_at = Column(DateTime(timezone=True), server_default='now()', nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    assigned_by_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # Relationships
    user = relationship('User', foreign_keys=[user_id])
    role = relationship('Role')
    assigned_by = relationship('User', foreign_keys=[assigned_by_id])
    
    @property
    def is_expired(self) -> bool:
        """Check if role assignment has expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


class RolePermission(Base):
    """Role-Permission association"""
    
    __tablename__ = 'role_permission_details'
    
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id'), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey('permissions.id'), nullable=False)
    granted_at = Column(DateTime(timezone=True), server_default='now()', nullable=False)
    granted_by_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # Relationships
    role = relationship('Role')
    permission = relationship('Permission')
    granted_by = relationship('User')