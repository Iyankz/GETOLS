"""
GETOLS User Service
Handles user management operations.
"""

from typing import Optional, List, Tuple
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.user import User, UserRole
from app.core.security import (
    hash_password,
    verify_password,
    validate_password_policy,
)


class UserService:
    """Service for user management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination."""
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def get_active_users(self) -> List[User]:
        """Get all active users."""
        return self.db.query(User).filter(User.is_active == True).all()
    
    def count(self) -> int:
        """Get total user count."""
        return self.db.query(User).count()
    
    def count_by_role(self, role: UserRole) -> int:
        """Get user count by role."""
        return self.db.query(User).filter(User.role == role).count()
    
    def create(
        self,
        username: str,
        password: str,
        role: UserRole,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        must_change_password: bool = True,
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Create a new user.
        
        Returns:
            Tuple of (User, error_message)
        """
        # Check if username already exists
        if self.get_by_username(username):
            return None, "Username already exists"
        
        # Check if email already exists (if provided)
        if email and self.get_by_email(email):
            return None, "Email already exists"
        
        # Validate password policy
        is_valid, error = validate_password_policy(password)
        if not is_valid:
            return None, error
        
        # Create user
        user = User(
            username=username,
            password_hash=hash_password(password),
            role=role,
            email=email,
            full_name=full_name,
            must_change_password=must_change_password,
            is_active=True,
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user, None
    
    def update(
        self,
        user_id: int,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Update user information.
        
        Returns:
            Tuple of (User, error_message)
        """
        user = self.get_by_id(user_id)
        if not user:
            return None, "User not found"
        
        # Check email uniqueness if changing
        if email and email != user.email:
            existing = self.get_by_email(email)
            if existing:
                return None, "Email already exists"
            user.email = email
        
        if full_name is not None:
            user.full_name = full_name
        
        if role is not None:
            user.role = role
        
        if is_active is not None:
            user.is_active = is_active
        
        self.db.commit()
        self.db.refresh(user)
        
        return user, None
    
    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Change user password.
        
        Returns:
            Tuple of (success, error_message)
        """
        user = self.get_by_id(user_id)
        if not user:
            return False, "User not found"
        
        # Verify current password
        if not verify_password(current_password, user.password_hash):
            return False, "Current password is incorrect"
        
        # Validate new password policy
        is_valid, error = validate_password_policy(new_password)
        if not is_valid:
            return False, error
        
        # Update password
        user.password_hash = hash_password(new_password)
        user.must_change_password = False
        
        self.db.commit()
        
        return True, None
    
    def reset_password(
        self,
        user_id: int,
        new_password: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Reset user password (admin action).
        
        Returns:
            Tuple of (success, error_message)
        """
        user = self.get_by_id(user_id)
        if not user:
            return False, "User not found"
        
        # Validate new password policy
        is_valid, error = validate_password_policy(new_password)
        if not is_valid:
            return False, error
        
        # Update password
        user.password_hash = hash_password(new_password)
        user.must_change_password = True  # Force password change on next login
        
        self.db.commit()
        
        return True, None
    
    def delete(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Delete a user.
        
        Returns:
            Tuple of (success, error_message)
        """
        user = self.get_by_id(user_id)
        if not user:
            return False, "User not found"
        
        # Prevent deleting the last admin
        if user.role == UserRole.ADMIN:
            admin_count = self.count_by_role(UserRole.ADMIN)
            if admin_count <= 1:
                return False, "Cannot delete the last admin user"
        
        self.db.delete(user)
        self.db.commit()
        
        return True, None
    
    def update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp."""
        user = self.get_by_id(user_id)
        if user:
            user.last_login = datetime.utcnow()
            self.db.commit()
    
    def search(self, query: str) -> List[User]:
        """Search users by username, email, or full name."""
        search_term = f"%{query}%"
        return self.db.query(User).filter(
            or_(
                User.username.ilike(search_term),
                User.email.ilike(search_term),
                User.full_name.ilike(search_term),
            )
        ).all()
    
    @staticmethod
    def create_default_admin(db: Session) -> Tuple[Optional[User], Optional[str]]:
        """
        Create default admin user if no users exist.
        Password is generated randomly for security.
        
        Returns:
            Tuple of (Created user, generated_password) or (None, None) if users already exist
        """
        from app.core.security import generate_random_password
        
        # Check if any users exist
        if db.query(User).count() > 0:
            return None, None
        
        # Generate secure random password
        generated_password = generate_random_password(length=16)
        
        # Create default admin
        admin = User(
            username="admin",
            password_hash=hash_password(generated_password),
            role=UserRole.ADMIN,
            full_name="System Administrator",
            must_change_password=True,  # Force password change on first login
            is_active=True,
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        return admin, generated_password
