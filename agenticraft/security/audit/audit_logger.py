"""
Audit logging for AgentiCraft security.

This module provides comprehensive audit logging for security events,
compliance tracking, and forensic analysis.
"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager
import asyncio
import uuid


class AuditEventType(Enum):
    """Types of audit events."""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_CREATED = "token_created"
    TOKEN_REVOKED = "token_revoked"
    
    # Authorization events
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_CHANGED = "permission_changed"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REVOKED = "role_revoked"
    
    # Execution events
    AGENT_EXECUTED = "agent_executed"
    WORKFLOW_EXECUTED = "workflow_executed"
    TOOL_EXECUTED = "tool_executed"
    SANDBOX_EXECUTED = "sandbox_executed"
    
    # Data events
    DATA_ACCESSED = "data_accessed"
    DATA_MODIFIED = "data_modified"
    DATA_DELETED = "data_deleted"
    DATA_EXPORTED = "data_exported"
    
    # Security events
    SECURITY_ALERT = "security_alert"
    POLICY_VIOLATION = "policy_violation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    
    # System events
    CONFIG_CHANGED = "config_changed"
    SYSTEM_ERROR = "system_error"


class AuditSeverity(Enum):
    """Severity levels for audit events."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Represents an audit event."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    event_type: AuditEventType = AuditEventType.ACCESS_GRANTED
    severity: AuditSeverity = AuditSeverity.INFO
    user_id: Optional[str] = None
    username: Optional[str] = None
    session_id: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    result: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "user_id": self.user_id,
            "username": self.username,
            "session_id": self.session_id,
            "resource": self.resource,
            "action": self.action,
            "result": self.result,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "details": json.dumps(self.details),
            "error_message": self.error_message
        }


class AuditLogger:
    """Comprehensive audit logging system."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize audit logger.
        
        Args:
            db_path: Path to SQLite database for audit logs
        """
        if db_path is None:
            db_path = Path.home() / ".agenticraft" / "audit.db"
            
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # In-memory buffer for performance
        self._buffer: List[AuditEvent] = []
        self._buffer_size = 100
        self._flush_task = None
        
    def _init_database(self):
        """Initialize SQLite database for audit logs."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    user_id TEXT,
                    username TEXT,
                    session_id TEXT,
                    resource TEXT,
                    action TEXT,
                    result TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    details TEXT,
                    error_message TEXT
                )
            """)
            
            # Create indexes for common queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_logs(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON audit_logs(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON audit_logs(event_type)")
            
    async def log_event(self, event: AuditEvent):
        """Log an audit event."""
        # Add to buffer
        self._buffer.append(event)
        
        # Flush if buffer is full
        if len(self._buffer) >= self._buffer_size:
            await self.flush()
            
    async def flush(self):
        """Flush buffered events to database."""
        if not self._buffer:
            return
            
        events_to_write = self._buffer.copy()
        self._buffer.clear()
        
        # Write to database
        with sqlite3.connect(self.db_path) as conn:
            for event in events_to_write:
                conn.execute("""
                    INSERT INTO audit_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id,
                    event.timestamp.isoformat(),
                    event.event_type.value,
                    event.severity.value,
                    event.user_id,
                    event.username,
                    event.session_id,
                    event.resource,
                    event.action,
                    event.result,
                    event.ip_address,
                    event.user_agent,
                    json.dumps(event.details),
                    event.error_message
                ))
            conn.commit()
            
    async def log_authentication(
        self,
        success: bool,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        method: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Log authentication event."""
        event = AuditEvent(
            event_type=AuditEventType.LOGIN_SUCCESS if success else AuditEventType.LOGIN_FAILURE,
            severity=AuditSeverity.INFO if success else AuditSeverity.WARNING,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            result="success" if success else "failure",
            details={"auth_method": method},
            error_message=error
        )
        await self.log_event(event)
        
    async def log_authorization(
        self,
        granted: bool,
        user_id: str,
        username: Optional[str] = None,
        resource: str = None,
        action: str = None,
        reason: Optional[str] = None
    ):
        """Log authorization event."""
        event = AuditEvent(
            event_type=AuditEventType.ACCESS_GRANTED if granted else AuditEventType.ACCESS_DENIED,
            severity=AuditSeverity.INFO if granted else AuditSeverity.WARNING,
            user_id=user_id,
            username=username,
            resource=resource,
            action=action,
            result="granted" if granted else "denied",
            details={"reason": reason} if reason else {}
        )
        await self.log_event(event)
        
    async def log_execution(
        self,
        execution_type: str,  # agent, workflow, tool, sandbox
        name: str,
        user_id: str,
        username: Optional[str] = None,
        success: bool = True,
        duration_ms: Optional[int] = None,
        error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log execution event."""
        event_type_map = {
            "agent": AuditEventType.AGENT_EXECUTED,
            "workflow": AuditEventType.WORKFLOW_EXECUTED,
            "tool": AuditEventType.TOOL_EXECUTED,
            "sandbox": AuditEventType.SANDBOX_EXECUTED
        }
        
        event = AuditEvent(
            event_type=event_type_map.get(execution_type, AuditEventType.AGENT_EXECUTED),
            severity=AuditSeverity.INFO if success else AuditSeverity.ERROR,
            user_id=user_id,
            username=username,
            resource=name,
            action="execute",
            result="success" if success else "failure",
            details={
                **(details or {}),
                "duration_ms": duration_ms,
                "execution_type": execution_type
            },
            error_message=error
        )
        await self.log_event(event)
        
    async def log_security_alert(
        self,
        alert_type: str,
        severity: AuditSeverity,
        user_id: Optional[str] = None,
        description: str = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log security alert."""
        event = AuditEvent(
            event_type=AuditEventType.SECURITY_ALERT,
            severity=severity,
            user_id=user_id,
            details={
                "alert_type": alert_type,
                "description": description,
                **(details or {})
            }
        )
        await self.log_event(event)
        
    @contextmanager
    async def audit_context(
        self,
        user_id: str,
        action: str,
        resource: str,
        username: Optional[str] = None
    ):
        """
        Context manager for auditing operations.
        
        Usage:
            async with audit_logger.audit_context(user_id, "execute", "workflow") as audit:
                # Do operation
                audit["status"] = "success"
        """
        audit_details = {}
        start_time = datetime.now()
        
        try:
            yield audit_details
            
            # Log successful operation
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            await self.log_execution(
                execution_type=resource,
                name=resource,
                user_id=user_id,
                username=username,
                success=True,
                duration_ms=duration_ms,
                details=audit_details
            )
            
        except Exception as e:
            # Log failed operation
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            await self.log_execution(
                execution_type=resource,
                name=resource,
                user_id=user_id,
                username=username,
                success=False,
                duration_ms=duration_ms,
                error=str(e),
                details=audit_details
            )
            raise
            
    async def query_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        severity: Optional[AuditSeverity] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditEvent]:
        """Query audit logs with filters."""
        # Build query
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
            
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
            
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
            
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type.value)
            
        if severity:
            query += " AND severity = ?"
            params.append(severity.value)
            
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        # Execute query
        events = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            
            for row in cursor:
                event = AuditEvent(
                    event_id=row["event_id"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    event_type=AuditEventType(row["event_type"]),
                    severity=AuditSeverity(row["severity"]),
                    user_id=row["user_id"],
                    username=row["username"],
                    session_id=row["session_id"],
                    resource=row["resource"],
                    action=row["action"],
                    result=row["result"],
                    ip_address=row["ip_address"],
                    user_agent=row["user_agent"],
                    details=json.loads(row["details"]) if row["details"] else {},
                    error_message=row["error_message"]
                )
                events.append(event)
                
        return events
        
    async def get_user_activity(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get user activity summary."""
        start_time = datetime.now() - timedelta(days=days)
        
        # Get all user events
        events = await self.query_logs(
            user_id=user_id,
            start_time=start_time,
            limit=1000
        )
        
        # Summarize activity
        summary = {
            "user_id": user_id,
            "period_days": days,
            "total_events": len(events),
            "login_count": sum(1 for e in events if e.event_type == AuditEventType.LOGIN_SUCCESS),
            "failed_logins": sum(1 for e in events if e.event_type == AuditEventType.LOGIN_FAILURE),
            "executions": sum(1 for e in events if "EXECUTED" in e.event_type.value),
            "access_denied": sum(1 for e in events if e.event_type == AuditEventType.ACCESS_DENIED),
            "last_activity": events[0].timestamp.isoformat() if events else None,
            "event_types": {}
        }
        
        # Count by event type
        for event in events:
            event_type = event.event_type.value
            summary["event_types"][event_type] = summary["event_types"].get(event_type, 0) + 1
            
        return summary
        
    async def detect_anomalies(
        self,
        user_id: str,
        window_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """Detect anomalous user behavior."""
        anomalies = []
        start_time = datetime.now() - timedelta(minutes=window_minutes)
        
        # Get recent events
        events = await self.query_logs(
            user_id=user_id,
            start_time=start_time
        )
        
        # Check for anomalies
        # 1. Too many failed logins
        failed_logins = sum(1 for e in events if e.event_type == AuditEventType.LOGIN_FAILURE)
        if failed_logins > 5:
            anomalies.append({
                "type": "excessive_failed_logins",
                "severity": "high",
                "count": failed_logins,
                "description": f"User had {failed_logins} failed login attempts"
            })
            
        # 2. Unusual activity volume
        if len(events) > 100:
            anomalies.append({
                "type": "high_activity_volume",
                "severity": "medium",
                "count": len(events),
                "description": f"User generated {len(events)} events in {window_minutes} minutes"
            })
            
        # 3. Access denied patterns
        access_denied = sum(1 for e in events if e.event_type == AuditEventType.ACCESS_DENIED)
        if access_denied > 10:
            anomalies.append({
                "type": "excessive_access_denied",
                "severity": "high",
                "count": access_denied,
                "description": f"User had {access_denied} access denied events"
            })
            
        return anomalies
