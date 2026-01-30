"""
GETOLS Activity Service
Handles activity logging for audit trail.
"""

from typing import Optional, List
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.activity import ActivityLog, ActionType, AccessType


class ActivityService:
    """Service for activity logging and audit trail."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, log_id: int) -> Optional[ActivityLog]:
        """Get activity log by ID."""
        return self.db.query(ActivityLog).filter(ActivityLog.id == log_id).first()
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        action_type: Optional[ActionType] = None,
        user_id: Optional[int] = None,
        target_type: Optional[str] = None,
        success: Optional[bool] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[ActivityLog]:
        """
        Get activity logs with filtering and pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            action_type: Filter by action type
            user_id: Filter by user ID
            target_type: Filter by target type
            success: Filter by success status
            start_date: Filter by start date
            end_date: Filter by end date
        """
        query = self.db.query(ActivityLog)
        
        if action_type:
            query = query.filter(ActivityLog.action == action_type)
        
        if user_id:
            query = query.filter(ActivityLog.user_id == user_id)
        
        if target_type:
            query = query.filter(ActivityLog.target_type == target_type)
        
        if success is not None:
            query = query.filter(ActivityLog.success == (1 if success else 0))
        
        if start_date:
            query = query.filter(ActivityLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(ActivityLog.timestamp <= end_date)
        
        return query.order_by(desc(ActivityLog.timestamp)).offset(skip).limit(limit).all()
    
    def get_recent(self, limit: int = 50) -> List[ActivityLog]:
        """Get most recent activity logs."""
        return self.db.query(ActivityLog).order_by(
            desc(ActivityLog.timestamp)
        ).limit(limit).all()
    
    def get_by_user(self, user_id: int, limit: int = 100) -> List[ActivityLog]:
        """Get activity logs for a specific user."""
        return self.db.query(ActivityLog).filter(
            ActivityLog.user_id == user_id
        ).order_by(desc(ActivityLog.timestamp)).limit(limit).all()
    
    def get_by_target(
        self,
        target_type: str,
        target_id: int,
        limit: int = 100,
    ) -> List[ActivityLog]:
        """Get activity logs for a specific target."""
        return self.db.query(ActivityLog).filter(
            ActivityLog.target_type == target_type,
            ActivityLog.target_id == target_id,
        ).order_by(desc(ActivityLog.timestamp)).limit(limit).all()
    
    def count(
        self,
        action_type: Optional[ActionType] = None,
        success: Optional[bool] = None,
    ) -> int:
        """Get activity log count."""
        query = self.db.query(ActivityLog)
        
        if action_type:
            query = query.filter(ActivityLog.action == action_type)
        
        if success is not None:
            query = query.filter(ActivityLog.success == (1 if success else 0))
        
        return query.count()
    
    def log(
        self,
        user_id: Optional[int],
        username: str,
        role: str,
        action: ActionType,
        success: bool,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        target_name: Optional[str] = None,
        access_type: AccessType = AccessType.NONE,
        action_detail: Optional[str] = None,
        error_message: Optional[str] = None,
        extra_data: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ActivityLog:
        """
        Create a new activity log entry.
        
        Args:
            user_id: User ID (can be None for system actions)
            username: Username
            role: User role
            action: Action type
            success: Whether action was successful
            target_type: Type of target (e.g., "olt", "onu", "user")
            target_id: Target ID
            target_name: Target name (for display)
            access_type: OLT access type used (RO/RW/SNMP)
            action_detail: Human-readable action description
            error_message: Error message if failed
            extra_data: Additional data as JSON
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Created ActivityLog entry
        """
        log_entry = ActivityLog.create_log(
            user_id=user_id,
            username=username,
            role=role,
            action=action,
            success=success,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            access_type=access_type,
            action_detail=action_detail,
            error_message=error_message,
            extra_data=extra_data,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)
        
        return log_entry
    
    def log_login(
        self,
        user_id: int,
        username: str,
        role: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> ActivityLog:
        """Log a login attempt."""
        action = ActionType.LOGIN if success else ActionType.LOGIN_FAILED
        return self.log(
            user_id=user_id if success else None,
            username=username,
            role=role,
            action=action,
            success=success,
            action_detail=f"User {username} {'logged in' if success else 'failed to log in'}",
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    def log_logout(
        self,
        user_id: int,
        username: str,
        role: str,
        ip_address: Optional[str] = None,
    ) -> ActivityLog:
        """Log a logout."""
        return self.log(
            user_id=user_id,
            username=username,
            role=role,
            action=ActionType.LOGOUT,
            success=True,
            action_detail=f"User {username} logged out",
            ip_address=ip_address,
        )
    
    def log_olt_action(
        self,
        user_id: int,
        username: str,
        role: str,
        action: ActionType,
        olt_id: int,
        olt_name: str,
        success: bool,
        access_type: AccessType = AccessType.NONE,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> ActivityLog:
        """Log an OLT-related action."""
        return self.log(
            user_id=user_id,
            username=username,
            role=role,
            action=action,
            success=success,
            target_type="olt",
            target_id=olt_id,
            target_name=olt_name,
            access_type=access_type,
            action_detail=f"{action.value} on OLT {olt_name}",
            error_message=error_message,
            ip_address=ip_address,
        )
    
    def log_onu_action(
        self,
        user_id: int,
        username: str,
        role: str,
        action: ActionType,
        onu_id: int,
        onu_serial: str,
        olt_name: str,
        success: bool,
        access_type: AccessType = AccessType.NONE,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        extra_data: Optional[dict] = None,
    ) -> ActivityLog:
        """Log an ONU-related action."""
        return self.log(
            user_id=user_id,
            username=username,
            role=role,
            action=action,
            success=success,
            target_type="onu",
            target_id=onu_id,
            target_name=f"{onu_serial} ({olt_name})",
            access_type=access_type,
            action_detail=f"{action.value} ONU {onu_serial} on {olt_name}",
            error_message=error_message,
            ip_address=ip_address,
            extra_data=extra_data,
        )
    
    def log_security_violation(
        self,
        user_id: Optional[int],
        username: str,
        role: str,
        detail: str,
        ip_address: Optional[str] = None,
        extra_data: Optional[dict] = None,
    ) -> ActivityLog:
        """Log a security violation."""
        return self.log(
            user_id=user_id,
            username=username,
            role=role,
            action=ActionType.SECURITY_VIOLATION,
            success=False,
            action_detail=detail,
            ip_address=ip_address,
            extra_data=extra_data,
        )
    
    def cleanup_old_logs(self, days: int) -> int:
        """
        Delete logs older than specified days.
        
        Returns:
            Number of deleted logs
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        deleted = self.db.query(ActivityLog).filter(
            ActivityLog.timestamp < cutoff_date
        ).delete()
        
        self.db.commit()
        
        return deleted
    
    def get_statistics(self, days: int = 30) -> dict:
        """Get activity statistics for the specified period."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(ActivityLog).filter(ActivityLog.timestamp >= start_date)
        
        total = query.count()
        successful = query.filter(ActivityLog.success == 1).count()
        failed = query.filter(ActivityLog.success == 0).count()
        
        # Count by action type
        action_counts = {}
        for action in ActionType:
            count = query.filter(ActivityLog.action == action).count()
            if count > 0:
                action_counts[action.value] = count
        
        return {
            "period_days": days,
            "total": total,
            "successful": successful,
            "failed": failed,
            "by_action": action_counts,
        }
