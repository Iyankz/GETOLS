"""
GETOLS Auth Service
Handles authentication and session management.
"""

from typing import Optional, Tuple
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.session import UserSession
from app.core import settings
from app.core.security import (
    verify_password,
    create_session_token,
    verify_session_token,
    generate_session_id,
)
from app.services.user_service import UserService


class AuthService:
    """Service for authentication and session management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)
    
    def authenticate(
        self,
        username: str,
        password: str,
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Authenticate a user by username and password.
        
        Returns:
            Tuple of (User, error_message)
        """
        user = self.user_service.get_by_username(username)
        
        if not user:
            return None, "Invalid username or password"
        
        if not user.is_active:
            return None, "User account is disabled"
        
        if not verify_password(password, user.password_hash):
            return None, "Invalid username or password"
        
        return user, None
    
    def create_session(
        self,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> UserSession:
        """
        Create a new session for a user.
        
        Invalidates any existing sessions for the user (single session enforcement).
        """
        # Invalidate existing sessions
        self.invalidate_user_sessions(user.id)
        
        # Generate session credentials
        session_id = generate_session_id()
        session_token = create_session_token(
            user_id=user.id,
            username=user.username,
            role=user.role.value,
        )
        
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(minutes=settings.session_lifetime)
        
        # Create session record
        session = UserSession(
            user_id=user.id,
            session_id=session_id,
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        # Update last login
        self.user_service.update_last_login(user.id)
        
        return session
    
    def validate_session(self, session_id: str) -> Tuple[Optional[User], Optional[str]]:
        """
        Validate a session by session ID.
        
        Returns:
            Tuple of (User, error_message)
        """
        session = self.db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()
        
        if not session:
            return None, "Session not found"
        
        # Check expiration
        if session.is_expired:
            self.db.delete(session)
            self.db.commit()
            return None, "Session expired"
        
        # Verify token
        token_data = verify_session_token(session.session_token)
        if not token_data:
            self.db.delete(session)
            self.db.commit()
            return None, "Invalid session token"
        
        # Get user and keep it attached to session
        user = self.db.query(User).filter(User.id == session.user_id).first()
        if not user:
            self.db.delete(session)
            self.db.commit()
            return None, "User not found"
        
        if not user.is_active:
            self.db.delete(session)
            self.db.commit()
            return None, "User account is disabled"
        
        # Update last activity
        session.update_activity()
        self.db.commit()
        
        # Refresh user to ensure it's attached to current session
        self.db.refresh(user)
        
        return user, None
    
    def invalidate_session(self, session_id: str) -> bool:
        """
        Invalidate a specific session.
        
        Returns:
            True if session was found and deleted
        """
        session = self.db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()
        
        if session:
            self.db.delete(session)
            self.db.commit()
            return True
        
        return False
    
    def invalidate_user_sessions(self, user_id: int) -> int:
        """
        Invalidate all sessions for a user.
        
        Returns:
            Number of sessions deleted
        """
        deleted = self.db.query(UserSession).filter(
            UserSession.user_id == user_id
        ).delete()
        
        self.db.commit()
        
        return deleted
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions.
        
        Returns:
            Number of sessions deleted
        """
        deleted = self.db.query(UserSession).filter(
            UserSession.expires_at < datetime.utcnow()
        ).delete()
        
        self.db.commit()
        
        return deleted
    
    def get_active_sessions_count(self) -> int:
        """Get count of active (non-expired) sessions."""
        return self.db.query(UserSession).filter(
            UserSession.expires_at > datetime.utcnow()
        ).count()
    
    def extend_session(self, session_id: str) -> bool:
        """
        Extend a session's expiration time.
        
        Returns:
            True if session was found and extended
        """
        session = self.db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()
        
        if session and not session.is_expired:
            session.expires_at = datetime.utcnow() + timedelta(minutes=settings.session_lifetime)
            session.update_activity()
            self.db.commit()
            return True
        
        return False
