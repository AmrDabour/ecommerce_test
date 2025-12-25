"""
Admin Views - SQLAdmin Model Views for admin_db only
Only shows tables that exist in admin_db database
"""

from sqladmin import ModelView
from models_admin import Notification, Message, AuditLog, SystemSetting


class NotificationAdmin(ModelView, model=Notification):
    column_list = [
        Notification.id,
        Notification.user_id,
        Notification.type,
        Notification.title,
        Notification.is_read,
        Notification.created_at
    ]
    column_searchable_list = [Notification.title, Notification.message]
    column_sortable_list = [Notification.id, Notification.created_at, Notification.type]
    form_excluded_columns = [Notification.created_at]

    name = "Notification"
    name_plural = "Notifications"
    icon = "fa-solid fa-bell"


class MessageAdmin(ModelView, model=Message):
    column_list = [
        Message.id,
        Message.sender_id,
        Message.receiver_id,
        Message.subject,
        Message.is_read,
        Message.created_at
    ]
    column_searchable_list = [Message.subject, Message.message]  # Changed from 'body' to 'message'
    column_sortable_list = [Message.id, Message.created_at]
    form_excluded_columns = [Message.created_at]

    name = "Message"
    name_plural = "Messages"
    icon = "fa-solid fa-envelope"


class AuditLogAdmin(ModelView, model=AuditLog):
    column_list = [
        AuditLog.id,
        AuditLog.admin_user_id,  # Changed from user_id to admin_user_id
        AuditLog.action,
        AuditLog.entity_type,
        AuditLog.entity_id,
        AuditLog.created_at
    ]
    column_searchable_list = [AuditLog.action, AuditLog.entity_type]
    column_sortable_list = [AuditLog.id, AuditLog.created_at, AuditLog.action]
    form_excluded_columns = [AuditLog.created_at]

    # Read-only for audit logs
    can_create = False
    can_edit = False
    can_delete = False

    name = "Audit Log"
    name_plural = "Audit Logs"
    icon = "fa-solid fa-file-alt"


class SystemSettingAdmin(ModelView, model=SystemSetting):
    column_list = [
        SystemSetting.id,
        SystemSetting.key,
        SystemSetting.value,
        SystemSetting.description,
        SystemSetting.updated_by,
        SystemSetting.updated_at
    ]
    column_searchable_list = [SystemSetting.key, SystemSetting.description]
    column_sortable_list = [SystemSetting.id, SystemSetting.key, SystemSetting.updated_at]
    form_excluded_columns = [SystemSetting.updated_at]

    name = "System Setting"
    name_plural = "System Settings"
    icon = "fa-solid fa-cog"


def register_admin_views(admin):
    """Register admin views for admin_db tables only"""
    admin.add_view(NotificationAdmin)
    admin.add_view(MessageAdmin)
    admin.add_view(AuditLogAdmin)
    admin.add_view(SystemSettingAdmin)

    print("✅ Registered admin views for admin_db tables")
    print("   - Notifications, Messages, Audit Logs, System Settings")
    print("")
    print("ℹ️  For User/Product/Order management:")
    print("   - Use respective service APIs (Auth, Product, Order services)")
    print("   - Or implement PostgreSQL Foreign Data Wrapper (FDW)")
