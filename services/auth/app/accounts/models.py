from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator


class UserRole(models.TextChoices):
    """User role types in the system"""
    ADMIN = 'ADMIN', _('Admin')
    VENDOR = 'VENDOR', _('Vendor')
    CUSTOMER = 'CUSTOMER', _('Customer')


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with an email and password"""
        if not email:
            raise ValueError(_('The Email field must be set'))
        
        email = self.normalize_email(email)
        extra_fields.setdefault('role', UserRole.CUSTOMER)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_vendor(self, email, password=None, **extra_fields):
        """Create and return a vendor user"""
        extra_fields.setdefault('role', UserRole.VENDOR)
        extra_fields.setdefault('is_active', False)  # Vendors need approval
        return self.create_user(email, password, **extra_fields)
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with admin privileges"""
        extra_fields.setdefault('role', UserRole.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with email-based authentication.
    Supports three roles: Admin, Vendor, and Customer.
    """
    
    email = models.EmailField(
        _('email address'),
        unique=True,
        db_index=True,
        error_messages={
            'unique': _('A user with that email already exists.'),
        }
    )
    
    role = models.CharField(
        _('role'),
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER,
        db_index=True
    )
    
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    )
    phone_number = models.CharField(
        _('phone number'),
        validators=[phone_regex],
        max_length=17,
        blank=True,
        null=True
    )
    
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    
    email_verified = models.BooleanField(
        _('email verified'),
        default=False,
        help_text=_('Designates whether this user has verified their email address.')
    )
    
    created_at = models.DateTimeField(_('date joined'), auto_now_add=True)
    updated_at = models.DateTimeField(_('last updated'), auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email is already the USERNAME_FIELD
    
    class Meta:
        db_table = 'users'
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'role']),
            models.Index(fields=['is_active', 'role']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between"""
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name or self.email
    
    def get_short_name(self):
        """Return the short name for the user"""
        return self.first_name or self.email.split('@')[0]
    
    @property
    def is_admin(self):
        """Check if user is an admin"""
        return self.role == UserRole.ADMIN
    
    @property
    def is_vendor(self):
        """Check if user is a vendor"""
        return self.role == UserRole.VENDOR
    
    @property
    def is_customer(self):
        """Check if user is a customer"""
        return self.role == UserRole.CUSTOMER


class VendorProfile(models.Model):
    """
    Extended profile for vendor users.
    Contains business information and approval status.
    """
    
    class VendorStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending Approval')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')
        SUSPENDED = 'SUSPENDED', _('Suspended')
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='vendor_profile',
        limit_choices_to={'role': UserRole.VENDOR}
    )
    
    business_name = models.CharField(
        _('business name'),
        max_length=255,
        unique=True,
        db_index=True
    )
    
    business_description = models.TextField(
        _('business description'),
        blank=True,
        help_text=_('Describe your business and the products you sell')
    )
    
    business_registration_number = models.CharField(
        _('business registration number'),
        max_length=100,
        blank=True,
        help_text=_('Official business registration or tax ID')
    )
    
    business_email = models.EmailField(
        _('business email'),
        blank=True,
        help_text=_('Official business contact email')
    )
    
    business_phone = models.CharField(
        _('business phone'),
        max_length=17,
        blank=True
    )
    
    business_address = models.TextField(_('business address'), blank=True)
    business_city = models.CharField(_('city'), max_length=100, blank=True)
    business_state = models.CharField(_('state/province'), max_length=100, blank=True)
    business_country = models.CharField(_('country'), max_length=100, blank=True)
    business_postal_code = models.CharField(_('postal code'), max_length=20, blank=True)
    
    logo = models.ImageField(
        _('business logo'),
        upload_to='vendor_logos/%Y/%m/',
        blank=True,
        null=True
    )
    
    banner = models.ImageField(
        _('store banner'),
        upload_to='vendor_banners/%Y/%m/',
        blank=True,
        null=True
    )
    
    status = models.CharField(
        _('vendor status'),
        max_length=20,
        choices=VendorStatus.choices,
        default=VendorStatus.PENDING,
        db_index=True
    )
    
    commission_rate = models.DecimalField(
        _('commission rate'),
        max_digits=5,
        decimal_places=2,
        default=10.00,
        help_text=_('Platform commission percentage (0-100)')
    )
    
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_vendors',
        limit_choices_to={'role': UserRole.ADMIN}
    )
    
    approved_at = models.DateTimeField(_('approved at'), null=True, blank=True)
    rejection_reason = models.TextField(_('rejection reason'), blank=True)
    
    total_sales = models.DecimalField(
        _('total sales'),
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text=_('Lifetime sales amount')
    )
    
    total_products = models.PositiveIntegerField(
        _('total products'),
        default=0,
        help_text=_('Total number of approved products')
    )
    
    is_featured = models.BooleanField(
        _('featured vendor'),
        default=False,
        help_text=_('Display this vendor in featured sections')
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'vendor_profiles'
        verbose_name = _('vendor profile')
        verbose_name_plural = _('vendor profiles')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_featured']),
            models.Index(fields=['business_name']),
        ]
    
    def __str__(self):
        return f'{self.business_name} ({self.user.email})'
    
    @property
    def is_approved(self):
        """Check if vendor is approved"""
        return self.status == self.VendorStatus.APPROVED
    
    @property
    def is_active(self):
        """Check if vendor can operate (approved and user is active)"""
        return self.is_approved and self.user.is_active


class CustomerProfile(models.Model):
    """
    Extended profile for customer users.
    Contains preferences and loyalty information.
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='customer_profile',
        limit_choices_to={'role': UserRole.CUSTOMER}
    )
    
    date_of_birth = models.DateField(
        _('date of birth'),
        null=True,
        blank=True
    )
    
    avatar = models.ImageField(
        _('profile picture'),
        upload_to='customer_avatars/%Y/%m/',
        blank=True,
        null=True
    )
    
    # Loyalty & Marketing
    loyalty_points = models.PositiveIntegerField(
        _('loyalty points'),
        default=0,
        help_text=_('Points earned from purchases')
    )
    
    newsletter_subscribed = models.BooleanField(
        _('newsletter subscription'),
        default=False
    )
    
    # Shopping Stats
    total_orders = models.PositiveIntegerField(
        _('total orders'),
        default=0
    )
    
    total_spent = models.DecimalField(
        _('total amount spent'),
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    
    # Preferences
    preferred_currency = models.CharField(
        _('preferred currency'),
        max_length=3,
        default='USD',
        help_text=_('ISO 4217 currency code')
    )
    
    preferred_language = models.CharField(
        _('preferred language'),
        max_length=10,
        default='en',
        help_text=_('Language code (e.g., en, fr, es)')
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'customer_profiles'
        verbose_name = _('customer profile')
        verbose_name_plural = _('customer profiles')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['loyalty_points']),
            models.Index(fields=['total_orders']),
        ]
    
    def __str__(self):
        return f'{self.user.get_full_name()} - Customer Profile'


class Address(models.Model):
    """
    Reusable address model for both shipping and billing.
    Linked to users (customers and vendors).
    """
    
    class AddressType(models.TextChoices):
        SHIPPING = 'SHIPPING', _('Shipping Address')
        BILLING = 'BILLING', _('Billing Address')
        BOTH = 'BOTH', _('Shipping & Billing')
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses',
        db_index=True
    )
    
    address_type = models.CharField(
        _('address type'),
        max_length=20,
        choices=AddressType.choices,
        default=AddressType.SHIPPING
    )
    
    full_name = models.CharField(_('full name'), max_length=255)
    phone_number = models.CharField(_('phone number'), max_length=17)
    
    address_line1 = models.CharField(_('address line 1'), max_length=255)
    address_line2 = models.CharField(_('address line 2'), max_length=255, blank=True)
    
    city = models.CharField(_('city'), max_length=100)
    state_province = models.CharField(_('state/province'), max_length=100)
    postal_code = models.CharField(_('postal code'), max_length=20)
    country = models.CharField(_('country'), max_length=100, db_index=True)
    
    is_default = models.BooleanField(
        _('default address'),
        default=False,
        help_text=_('Use this address by default')
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'addresses'
        verbose_name = _('address')
        verbose_name_plural = _('addresses')
        ordering = ['-is_default', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_default']),
            models.Index(fields=['user', 'address_type']),
            models.Index(fields=['country', 'city']),
        ]
    
    def __str__(self):
        return f'{self.full_name} - {self.city}, {self.country}'
