from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# Note: In microservices architecture, we use user_id instead of ForeignKey
# to reference users in the auth-service


class NotificationType(models.TextChoices):
    """Types of notifications in the system"""
    # Product notifications
    PRODUCT_APPROVED = 'PRODUCT_APPROVED', _('Product Approved')
    PRODUCT_REJECTED = 'PRODUCT_REJECTED', _('Product Rejected')
    PRODUCT_LOW_STOCK = 'PRODUCT_LOW_STOCK', _('Low Stock Alert')
    PRODUCT_OUT_OF_STOCK = 'PRODUCT_OUT_OF_STOCK', _('Out of Stock')
    
    # Order notifications
    ORDER_CREATED = 'ORDER_CREATED', _('Order Created')
    ORDER_PAID = 'ORDER_PAID', _('Order Paid')
    ORDER_SHIPPED = 'ORDER_SHIPPED', _('Order Shipped')
    ORDER_DELIVERED = 'ORDER_DELIVERED', _('Order Delivered')
    ORDER_CANCELLED = 'ORDER_CANCELLED', _('Order Cancelled')
    
    # Vendor notifications
    NEW_ORDER_ITEM = 'NEW_ORDER_ITEM', _('New Order Item for Vendor')
    VENDOR_APPROVED = 'VENDOR_APPROVED', _('Vendor Account Approved')
    VENDOR_REJECTED = 'VENDOR_REJECTED', _('Vendor Account Rejected')
    PAYOUT_PROCESSED = 'PAYOUT_PROCESSED', _('Payout Processed')
    
    # Payment notifications
    PAYMENT_SUCCEEDED = 'PAYMENT_SUCCEEDED', _('Payment Succeeded')
    PAYMENT_FAILED = 'PAYMENT_FAILED', _('Payment Failed')
    REFUND_PROCESSED = 'REFUND_PROCESSED', _('Refund Processed')
    
    # Review notifications
    NEW_REVIEW = 'NEW_REVIEW', _('New Product Review')
    REVIEW_REPLY = 'REVIEW_REPLY', _('Review Reply')
    
    # Return notifications
    RETURN_REQUESTED = 'RETURN_REQUESTED', _('Return Requested')
    RETURN_APPROVED = 'RETURN_APPROVED', _('Return Approved')
    RETURN_REJECTED = 'RETURN_REJECTED', _('Return Rejected')
    
    # System notifications
    WELCOME = 'WELCOME', _('Welcome Message')
    ACCOUNT_VERIFIED = 'ACCOUNT_VERIFIED', _('Account Verified')
    PASSWORD_CHANGED = 'PASSWORD_CHANGED', _('Password Changed')
    SECURITY_ALERT = 'SECURITY_ALERT', _('Security Alert')
    
    # Promotional
    PROMOTION = 'PROMOTION', _('Promotional Message')
    NEWSLETTER = 'NEWSLETTER', _('Newsletter')


class NotificationChannel(models.TextChoices):
    """Channels through which notifications can be sent"""
    IN_APP = 'IN_APP', _('In-App Notification')
    EMAIL = 'EMAIL', _('Email')
    SMS = 'SMS', _('SMS')
    PUSH = 'PUSH', _('Push Notification')


class Notification(models.Model):
    """
    In-app notifications for users.
    Real-time alerts shown in the application.
    """
    
    recipient_id = models.IntegerField(
        _('recipient user ID'),
        db_index=True,
        help_text=_('User ID from auth-service who receives this notification')
    )
    
    notification_type = models.CharField(
        _('notification type'),
        max_length=50,
        choices=NotificationType.choices,
        db_index=True
    )
    
    title = models.CharField(
        _('title'),
        max_length=255,
        help_text=_('Notification headline')
    )
    
    message = models.TextField(
        _('message'),
        help_text=_('Notification body text')
    )
    
    # Link to related object using generic foreign key
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text=_('Type of related object')
    )
    
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('ID of related object')
    )
    
    related_object = GenericForeignKey('content_type', 'object_id')
    
    # Action URL (where to navigate when clicked)
    action_url = models.CharField(
        _('action URL'),
        max_length=500,
        blank=True,
        help_text=_('URL to navigate to when notification is clicked')
    )
    
    # Status
    is_read = models.BooleanField(
        _('read'),
        default=False,
        db_index=True
    )
    
    read_at = models.DateTimeField(
        _('read at'),
        null=True,
        blank=True
    )
    
    # Priority
    is_important = models.BooleanField(
        _('important'),
        default=False,
        help_text=_('Mark as high priority')
    )
    
    # Metadata
    metadata = models.JSONField(
        _('metadata'),
        default=dict,
        blank=True,
        help_text=_('Additional data as JSON')
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient_id', 'is_read', '-created_at']),
            models.Index(fields=['recipient_id', 'notification_type']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f'User #{self.recipient_id} - {self.title}'
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class EmailNotification(models.Model):
    """
    Email notification log.
    Tracks all emails sent by the system.
    """
    
    class EmailStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        SENT = 'SENT', _('Sent')
        FAILED = 'FAILED', _('Failed')
        BOUNCED = 'BOUNCED', _('Bounced')
        OPENED = 'OPENED', _('Opened')
        CLICKED = 'CLICKED', _('Clicked')
    
    recipient_id = models.IntegerField(
        _('recipient user ID'),
        null=True,
        blank=True,
        db_index=True,
        help_text=_('User ID from auth-service who received this email')
    )
    
    recipient_email = models.EmailField(
        _('recipient email'),
        db_index=True,
        help_text=_('Email address where notification was sent')
    )
    
    notification_type = models.CharField(
        _('notification type'),
        max_length=50,
        choices=NotificationType.choices,
        db_index=True
    )
    
    subject = models.CharField(_('email subject'), max_length=500)
    
    body_text = models.TextField(
        _('plain text body'),
        help_text=_('Plain text version of email')
    )
    
    body_html = models.TextField(
        _('HTML body'),
        blank=True,
        help_text=_('HTML version of email')
    )
    
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=EmailStatus.choices,
        default=EmailStatus.PENDING,
        db_index=True
    )
    
    # Email service provider details
    provider_message_id = models.CharField(
        _('provider message ID'),
        max_length=255,
        blank=True,
        help_text=_('Message ID from email service (e.g., SendGrid, AWS SES)')
    )
    
    error_message = models.TextField(
        _('error message'),
        blank=True,
        help_text=_('Error details if sending failed')
    )
    
    # Tracking
    opened_at = models.DateTimeField(_('opened at'), null=True, blank=True)
    clicked_at = models.DateTimeField(_('clicked at'), null=True, blank=True)
    bounced_at = models.DateTimeField(_('bounced at'), null=True, blank=True)
    
    # Related object
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    sent_at = models.DateTimeField(_('sent at'), null=True, blank=True)
    
    class Meta:
        db_table = 'email_notifications'
        verbose_name = _('email notification')
        verbose_name_plural = _('email notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient_email', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['provider_message_id']),
        ]
    
    def __str__(self):
        return f'{self.recipient_email} - {self.subject}'


class NotificationPreference(models.Model):
    """
    User notification preferences.
    Allows users to control which notifications they receive and through which channels.
    """
    
    user_id = models.IntegerField(
        _('user ID'),
        primary_key=True,
        db_index=True,
        help_text=_('User ID from auth-service')
    )
    
    # Channel preferences
    email_enabled = models.BooleanField(
        _('email notifications enabled'),
        default=True
    )
    
    sms_enabled = models.BooleanField(
        _('SMS notifications enabled'),
        default=False
    )
    
    push_enabled = models.BooleanField(
        _('push notifications enabled'),
        default=True
    )
    
    # Notification type preferences
    order_notifications = models.BooleanField(
        _('order notifications'),
        default=True,
        help_text=_('Receive notifications about order updates')
    )
    
    product_notifications = models.BooleanField(
        _('product notifications'),
        default=True,
        help_text=_('Receive notifications about product approvals/stock')
    )
    
    payment_notifications = models.BooleanField(
        _('payment notifications'),
        default=True,
        help_text=_('Receive notifications about payments/refunds')
    )
    
    shipping_notifications = models.BooleanField(
        _('shipping notifications'),
        default=True,
        help_text=_('Receive notifications about shipment updates')
    )
    
    review_notifications = models.BooleanField(
        _('review notifications'),
        default=True,
        help_text=_('Receive notifications about product reviews')
    )
    
    promotional_notifications = models.BooleanField(
        _('promotional notifications'),
        default=False,
        help_text=_('Receive promotional offers and deals')
    )
    
    newsletter_enabled = models.BooleanField(
        _('newsletter enabled'),
        default=False,
        help_text=_('Receive newsletter emails')
    )
    
    # Frequency settings
    digest_enabled = models.BooleanField(
        _('digest mode'),
        default=False,
        help_text=_('Receive notifications as daily digest instead of real-time')
    )
    
    digest_time = models.TimeField(
        _('digest time'),
        null=True,
        blank=True,
        help_text=_('Time of day to send digest (e.g., 09:00)')
    )
    
    # Do Not Disturb
    quiet_hours_enabled = models.BooleanField(
        _('quiet hours enabled'),
        default=False,
        help_text=_('Disable notifications during certain hours')
    )
    
    quiet_hours_start = models.TimeField(
        _('quiet hours start'),
        null=True,
        blank=True,
        help_text=_('Start of quiet hours (e.g., 22:00)')
    )
    
    quiet_hours_end = models.TimeField(
        _('quiet hours end'),
        null=True,
        blank=True,
        help_text=_('End of quiet hours (e.g., 08:00)')
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'notification_preferences'
        verbose_name = _('notification preference')
        verbose_name_plural = _('notification preferences')
    
    def __str__(self):
        return f'Notification Preferences - {self.user.email}'


class EmailTemplate(models.Model):
    """
    Email templates for different notification types.
    Admin can customize email content.
    """
    
    notification_type = models.CharField(
        _('notification type'),
        max_length=50,
        choices=NotificationType.choices,
        unique=True,
        db_index=True
    )
    
    name = models.CharField(
        _('template name'),
        max_length=255,
        help_text=_('Human-readable name for this template')
    )
    
    subject_template = models.CharField(
        _('subject template'),
        max_length=500,
        help_text=_('Subject line (can use template variables like {{order_number}})')
    )
    
    body_text_template = models.TextField(
        _('plain text template'),
        help_text=_('Plain text email body with template variables')
    )
    
    body_html_template = models.TextField(
        _('HTML template'),
        blank=True,
        help_text=_('HTML email body with template variables')
    )
    
    # Available template variables (for documentation)
    available_variables = models.JSONField(
        _('available variables'),
        default=list,
        blank=True,
        help_text=_('List of variables that can be used in this template')
    )
    
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Use this template for notifications')
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'email_templates'
        verbose_name = _('email template')
        verbose_name_plural = _('email templates')
        ordering = ['notification_type']
    
    def __str__(self):
        return f'{self.name} ({self.notification_type})'


class SystemAnnouncement(models.Model):
    """
    Platform-wide announcements.
    Admin can broadcast messages to all users or specific roles.
    """
    
    class AnnouncementType(models.TextChoices):
        INFO = 'INFO', _('Information')
        WARNING = 'WARNING', _('Warning')
        MAINTENANCE = 'MAINTENANCE', _('Maintenance')
        FEATURE = 'FEATURE', _('New Feature')
        PROMOTION = 'PROMOTION', _('Promotion')
    
    title = models.CharField(_('title'), max_length=255)
    message = models.TextField(_('message'))
    
    announcement_type = models.CharField(
        _('type'),
        max_length=20,
        choices=AnnouncementType.choices,
        default=AnnouncementType.INFO
    )
    
    # Target audience
    target_all_users = models.BooleanField(
        _('target all users'),
        default=True,
        help_text=_('Show to all users')
    )
    
    target_admins = models.BooleanField(_('target admins'), default=False)
    target_vendors = models.BooleanField(_('target vendors'), default=False)
    target_customers = models.BooleanField(_('target customers'), default=False)
    
    # Display settings
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Show this announcement')
    )
    
    is_dismissible = models.BooleanField(
        _('dismissible'),
        default=True,
        help_text=_('Users can dismiss this announcement')
    )
    
    priority = models.PositiveSmallIntegerField(
        _('priority'),
        default=1,
        help_text=_('Higher priority shown first')
    )
    
    # Validity period
    valid_from = models.DateTimeField(_('valid from'))
    valid_until = models.DateTimeField(
        _('valid until'),
        null=True,
        blank=True,
        help_text=_('Leave blank for indefinite')
    )
    
    # Action link
    action_text = models.CharField(
        _('action button text'),
        max_length=100,
        blank=True,
        help_text=_('Text for action button (e.g., "Learn More")')
    )
    
    action_url = models.CharField(
        _('action URL'),
        max_length=500,
        blank=True,
        help_text=_('URL for action button')
    )
    
    created_by_id = models.IntegerField(
        _('created by user ID'),
        null=True,
        blank=True,
        db_index=True,
        help_text=_('Admin user ID from auth-service who created this announcement')
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'system_announcements'
        verbose_name = _('system announcement')
        verbose_name_plural = _('system announcements')
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['is_active', 'valid_from', 'valid_until']),
        ]
    
    def __str__(self):
        return self.title


class AnnouncementDismissal(models.Model):
    """
    Track which users have dismissed which announcements.
    """
    
    announcement = models.ForeignKey(
        SystemAnnouncement,
        on_delete=models.CASCADE,
        related_name='dismissals'
    )
    
    user_id = models.IntegerField(
        _('user ID'),
        db_index=True,
        help_text=_('User ID from auth-service')
    )
    
    dismissed_at = models.DateTimeField(_('dismissed at'), auto_now_add=True)
    
    class Meta:
        db_table = 'announcement_dismissals'
        verbose_name = _('announcement dismissal')
        verbose_name_plural = _('announcement dismissals')
        unique_together = [['announcement', 'user_id']]
        indexes = [
            models.Index(fields=['user_id', 'announcement']),
        ]
    
    def __str__(self):
        return f'User #{self.user_id} dismissed "{self.announcement.title}"'
