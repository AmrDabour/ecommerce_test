"""
Admin DB Models - Only tables in admin_db
For cross-database admin access, use API calls to respective services
"""

from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Notification(Base):
    """User notifications table (admin_db)"""
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)  # References auth_db.users.id
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text)
    link = Column(String(500))
    is_read = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return f"Notification: {self.title}"


class Message(Base):
    """User-to-user messages table (admin_db)"""
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, nullable=False)  # References auth_db.users.id
    receiver_id = Column(Integer, nullable=False)  # References auth_db.users.id
    subject = Column(String(255))
    message = Column(Text, nullable=False)  # Changed from 'body' to 'message' to match DB schema
    parent_message_id = Column(Integer)  # References messages.id
    is_read = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return f"Message: {self.subject}"


class AuditLog(Base):
    """Admin action audit logs (admin_db)"""
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True)
    admin_user_id = Column(Integer, nullable=False)  # References auth_db.users.id (changed from user_id)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)  # Made NOT NULL to match DB schema
    entity_id = Column(Integer)
    old_values = Column(JSON)
    new_values = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return f"AuditLog: {self.action} on {self.entity_type}"


class SystemSetting(Base):
    """System-wide settings (admin_db)"""
    __tablename__ = 'system_settings'

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    description = Column(Text)
    updated_at = Column(TIMESTAMP, server_default=func.now())
    updated_by = Column(Integer)  # References auth_db.users.id

    def __repr__(self):
        return f"Setting: {self.key} = {self.value}"
