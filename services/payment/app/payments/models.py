from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal

# Note: In microservices architecture, we use IDs instead of ForeignKey
# to reference entities in other services


class PaymentMethod(models.TextChoices):
    """Supported payment methods"""
    STRIPE_CARD = 'STRIPE_CARD', _('Credit/Debit Card (Stripe)')
    STRIPE_WALLET = 'STRIPE_WALLET', _('Digital Wallet (Stripe)')
    BANK_TRANSFER = 'BANK_TRANSFER', _('Bank Transfer')
    CASH_ON_DELIVERY = 'CASH_ON_DELIVERY', _('Cash on Delivery')
    OTHER = 'OTHER', _('Other')


class PaymentStatus(models.TextChoices):
    """Payment processing statuses"""
    PENDING = 'PENDING', _('Pending')
    PROCESSING = 'PROCESSING', _('Processing')
    SUCCEEDED = 'SUCCEEDED', _('Succeeded')
    FAILED = 'FAILED', _('Failed')
    CANCELLED = 'CANCELLED', _('Cancelled')
    REFUNDED = 'REFUNDED', _('Refunded')
    PARTIALLY_REFUNDED = 'PARTIALLY_REFUNDED', _('Partially Refunded')


class Payment(models.Model):
    """
    Payment transactions for orders.
    Integrates with Stripe and tracks all payment attempts.
    """
    
    # Payment Identification
    transaction_id = models.CharField(
        _('transaction ID'),
        max_length=255,
        unique=True,
        db_index=True,
        help_text=_('Unique payment transaction identifier')
    )
    
    # Relations (order_id from order-service, customer_id from auth-service)
    order_id = models.IntegerField(
        _('order ID'),
        db_index=True,
        help_text=_('Order ID from order-service')
    )
    
    customer_id = models.IntegerField(
        _('customer ID'),
        db_index=True,
        help_text=_('Customer user ID from auth-service')
    )
    
    # Payment Details
    payment_method = models.CharField(
        _('payment method'),
        max_length=30,
        choices=PaymentMethod.choices,
        db_index=True
    )
    
    status = models.CharField(
        _('payment status'),
        max_length=30,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True
    )
    
    # Amounts
    amount = models.DecimalField(
        _('payment amount'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    currency = models.CharField(
        _('currency'),
        max_length=3,
        default='USD',
        help_text=_('ISO 4217 currency code')
    )
    
    fee_amount = models.DecimalField(
        _('fee amount'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Payment gateway fees (Stripe fees)')
    )
    
    refunded_amount = models.DecimalField(
        _('refunded amount'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Stripe Integration
    stripe_payment_intent_id = models.CharField(
        _('Stripe Payment Intent ID'),
        max_length=255,
        blank=True,
        db_index=True,
        help_text=_('Stripe PaymentIntent ID (pi_xxx)')
    )
    
    stripe_charge_id = models.CharField(
        _('Stripe Charge ID'),
        max_length=255,
        blank=True,
        help_text=_('Stripe Charge ID (ch_xxx)')
    )
    
    stripe_customer_id = models.CharField(
        _('Stripe Customer ID'),
        max_length=255,
        blank=True,
        help_text=_('Stripe Customer ID (cus_xxx)')
    )
    
    stripe_payment_method_id = models.CharField(
        _('Stripe Payment Method ID'),
        max_length=255,
        blank=True,
        help_text=_('Stripe PaymentMethod ID (pm_xxx)')
    )
    
    # Card Details (last 4 digits for display, no sensitive data)
    card_brand = models.CharField(
        _('card brand'),
        max_length=50,
        blank=True,
        help_text=_('e.g., Visa, Mastercard, Amex')
    )
    
    card_last4 = models.CharField(
        _('card last 4 digits'),
        max_length=4,
        blank=True
    )
    
    card_exp_month = models.PositiveSmallIntegerField(
        _('card expiry month'),
        null=True,
        blank=True
    )
    
    card_exp_year = models.PositiveSmallIntegerField(
        _('card expiry year'),
        null=True,
        blank=True
    )
    
    # Additional Metadata
    description = models.TextField(_('description'), blank=True)
    
    failure_code = models.CharField(
        _('failure code'),
        max_length=100,
        blank=True,
        help_text=_('Error code if payment failed')
    )
    
    failure_message = models.TextField(
        _('failure message'),
        blank=True,
        help_text=_('Human-readable error message')
    )
    
    # Security & Fraud Detection
    ip_address = models.GenericIPAddressField(
        _('IP address'),
        null=True,
        blank=True
    )
    
    risk_score = models.PositiveSmallIntegerField(
        _('risk score'),
        null=True,
        blank=True,
        help_text=_('Fraud risk score (0-100, higher = riskier)')
    )
    
    # Receipts
    receipt_url = models.URLField(
        _('receipt URL'),
        blank=True,
        help_text=_('Link to payment receipt')
    )
    
    receipt_email = models.EmailField(
        _('receipt email'),
        blank=True,
        help_text=_('Email where receipt was sent')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    succeeded_at = models.DateTimeField(_('succeeded at'), null=True, blank=True)
    failed_at = models.DateTimeField(_('failed at'), null=True, blank=True)
    
    class Meta:
        db_table = 'payments'
        verbose_name = _('payment')
        verbose_name_plural = _('payments')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_id', 'status']),
            models.Index(fields=['customer_id', '-created_at']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['stripe_payment_intent_id']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f'Payment {self.transaction_id} - Order #{self.order_id}'
    
    @property
    def is_successful(self):
        """Check if payment succeeded"""
        return self.status == PaymentStatus.SUCCEEDED
    
    @property
    def net_amount(self):
        """Calculate net amount after fees"""
        return self.amount - self.fee_amount


class PaymentRefund(models.Model):
    """
    Payment refund transactions.
    Links payment refunds to order refund requests.
    """
    
    class RefundStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        PROCESSING = 'PROCESSING', _('Processing')
        SUCCEEDED = 'SUCCEEDED', _('Succeeded')
        FAILED = 'FAILED', _('Failed')
        CANCELLED = 'CANCELLED', _('Cancelled')
    
    # Refund Identification
    refund_transaction_id = models.CharField(
        _('refund transaction ID'),
        max_length=255,
        unique=True,
        db_index=True
    )
    
    # Relations
    payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        related_name='refunds',
        help_text=_('Original payment being refunded')
    )
    
    refund_request_id = models.IntegerField(
        _('refund request ID'),
        null=True,
        blank=True,
        db_index=True,
        help_text=_('Refund request ID from order-service')
    )
    
    # Refund Details
    status = models.CharField(
        _('refund status'),
        max_length=20,
        choices=RefundStatus.choices,
        default=RefundStatus.PENDING,
        db_index=True
    )
    
    amount = models.DecimalField(
        _('refund amount'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    currency = models.CharField(
        _('currency'),
        max_length=3,
        default='USD'
    )
    
    # Stripe Integration
    stripe_refund_id = models.CharField(
        _('Stripe Refund ID'),
        max_length=255,
        blank=True,
        db_index=True,
        help_text=_('Stripe Refund ID (re_xxx)')
    )
    
    reason = models.TextField(_('refund reason'), blank=True)
    
    failure_reason = models.TextField(
        _('failure reason'),
        blank=True,
        help_text=_('Why refund failed if applicable')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    succeeded_at = models.DateTimeField(_('succeeded at'), null=True, blank=True)
    
    class Meta:
        db_table = 'payment_refunds'
        verbose_name = _('payment refund')
        verbose_name_plural = _('payment refunds')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment', 'status']),
            models.Index(fields=['stripe_refund_id']),
            models.Index(fields=['refund_transaction_id']),
        ]
    
    def __str__(self):
        return f'Refund {self.refund_transaction_id} - {self.amount} {self.currency}'


class VendorPayout(models.Model):
    """
    Track payouts to vendors.
    Platform pays vendors after commission deduction.
    """
    
    class PayoutStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        PROCESSING = 'PROCESSING', _('Processing')
        PAID = 'PAID', _('Paid')
        FAILED = 'FAILED', _('Failed')
        CANCELLED = 'CANCELLED', _('Cancelled')
    
    # Payout Identification
    payout_number = models.CharField(
        _('payout number'),
        max_length=50,
        unique=True,
        db_index=True
    )
    
    vendor_id = models.IntegerField(
        _('vendor ID'),
        db_index=True,
        help_text=_('Vendor user ID from auth-service')
    )
    
    status = models.CharField(
        _('payout status'),
        max_length=20,
        choices=PayoutStatus.choices,
        default=PayoutStatus.PENDING,
        db_index=True
    )
    
    # Financial Details
    amount = models.DecimalField(
        _('payout amount'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Total amount to be paid to vendor')
    )
    
    currency = models.CharField(
        _('currency'),
        max_length=3,
        default='USD'
    )
    
    # Period covered by this payout
    period_start = models.DateField(
        _('period start'),
        help_text=_('Start date of sales period covered')
    )
    
    period_end = models.DateField(
        _('period end'),
        help_text=_('End date of sales period covered')
    )
    
    # Payment Method
    payment_method = models.CharField(
        _('payment method'),
        max_length=50,
        choices=[
            ('BANK_TRANSFER', _('Bank Transfer')),
            ('STRIPE_CONNECT', _('Stripe Connect')),
            ('PAYPAL', _('PayPal')),
            ('OTHER', _('Other')),
        ],
        default='BANK_TRANSFER'
    )
    
    # Bank/Payment Details (encrypted in production)
    bank_account_name = models.CharField(_('account name'), max_length=255, blank=True)
    bank_account_number = models.CharField(_('account number'), max_length=100, blank=True)
    bank_name = models.CharField(_('bank name'), max_length=255, blank=True)
    bank_routing_number = models.CharField(_('routing number'), max_length=50, blank=True)
    
    # Stripe Connect
    stripe_payout_id = models.CharField(
        _('Stripe Payout ID'),
        max_length=255,
        blank=True,
        help_text=_('Stripe payout ID (po_xxx)')
    )
    
    # Admin tracking
    processed_by_id = models.IntegerField(
        _('processed by user ID'),
        null=True,
        blank=True,
        db_index=True,
        help_text=_('Admin user ID from auth-service who processed this payout')
    )
    
    admin_note = models.TextField(_('admin note'), blank=True)
    
    # Transaction reference (e.g., wire transfer reference)
    transaction_reference = models.CharField(
        _('transaction reference'),
        max_length=255,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    paid_at = models.DateTimeField(_('paid at'), null=True, blank=True)
    
    class Meta:
        db_table = 'vendor_payouts'
        verbose_name = _('vendor payout')
        verbose_name_plural = _('vendor payouts')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vendor_id', 'status']),
            models.Index(fields=['payout_number']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f'Payout #{self.payout_number} - Vendor #{self.vendor_id} - {self.amount} {self.currency}'


class SavedPaymentMethod(models.Model):
    """
    Customer saved payment methods for faster checkout.
    Stores Stripe payment method IDs, not actual card data.
    """
    
    customer_id = models.IntegerField(
        _('customer ID'),
        db_index=True,
        help_text=_('Customer user ID from auth-service')
    )
    
    # Stripe Integration
    stripe_payment_method_id = models.CharField(
        _('Stripe Payment Method ID'),
        max_length=255,
        unique=True,
        db_index=True,
        help_text=_('Stripe PaymentMethod ID (pm_xxx)')
    )
    
    # Card Details (for display only)
    card_brand = models.CharField(
        _('card brand'),
        max_length=50,
        help_text=_('e.g., Visa, Mastercard')
    )
    
    card_last4 = models.CharField(
        _('last 4 digits'),
        max_length=4
    )
    
    card_exp_month = models.PositiveSmallIntegerField(_('expiry month'))
    card_exp_year = models.PositiveSmallIntegerField(_('expiry year'))
    
    # Preferences
    is_default = models.BooleanField(
        _('default payment method'),
        default=False,
        help_text=_('Use this as default payment method')
    )
    
    nickname = models.CharField(
        _('nickname'),
        max_length=100,
        blank=True,
        help_text=_('Optional name for this payment method')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    last_used_at = models.DateTimeField(_('last used'), null=True, blank=True)
    
    class Meta:
        db_table = 'saved_payment_methods'
        verbose_name = _('saved payment method')
        verbose_name_plural = _('saved payment methods')
        ordering = ['-is_default', '-last_used_at']
        indexes = [
            models.Index(fields=['customer_id', 'is_default']),
        ]
    
    def __str__(self):
        name = self.nickname or f'{self.card_brand} ending in {self.card_last4}'
        return f'Customer #{self.customer_id} - {name}'


class Coupon(models.Model):
    """
    Discount coupons and promo codes.
    Can be percentage or fixed amount discounts.
    """
    
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'PERCENTAGE', _('Percentage')
        FIXED_AMOUNT = 'FIXED_AMOUNT', _('Fixed Amount')
    
    # Coupon Identification
    code = models.CharField(
        _('coupon code'),
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_('Unique coupon code (e.g., SUMMER2024)')
    )
    
    name = models.CharField(
        _('coupon name'),
        max_length=255,
        help_text=_('Internal name for this coupon')
    )
    
    description = models.TextField(_('description'), blank=True)
    
    # Discount Details
    discount_type = models.CharField(
        _('discount type'),
        max_length=20,
        choices=DiscountType.choices
    )
    
    discount_value = models.DecimalField(
        _('discount value'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Percentage (e.g., 10 for 10%) or fixed amount (e.g., 5.00 for $5)')
    )
    
    max_discount_amount = models.DecimalField(
        _('max discount amount'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Maximum discount for percentage coupons')
    )
    
    # Usage Limits
    min_order_amount = models.DecimalField(
        _('minimum order amount'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Minimum order total required to use coupon')
    )
    
    max_uses = models.PositiveIntegerField(
        _('max total uses'),
        null=True,
        blank=True,
        help_text=_('Maximum total redemptions (null = unlimited)')
    )
    
    max_uses_per_customer = models.PositiveIntegerField(
        _('max uses per customer'),
        default=1,
        help_text=_('How many times one customer can use this')
    )
    
    current_uses = models.PositiveIntegerField(
        _('current uses'),
        default=0,
        help_text=_('Number of times coupon has been used')
    )
    
    # Validity Period
    valid_from = models.DateTimeField(_('valid from'))
    valid_until = models.DateTimeField(
        _('valid until'),
        null=True,
        blank=True,
        help_text=_('Leave blank for no expiration')
    )
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    
    # Created by (admin_id from auth-service)
    created_by_id = models.IntegerField(
        _('created by user ID'),
        null=True,
        blank=True,
        db_index=True,
        help_text=_('Admin user ID from auth-service who created this coupon')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'coupons'
        verbose_name = _('coupon')
        verbose_name_plural = _('coupons')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active', 'valid_from', 'valid_until']),
        ]
    
    def __str__(self):
        return f'{self.code} - {self.name}'
    
    @property
    def is_valid(self):
        """Check if coupon is currently valid"""
        from django.utils import timezone
        now = timezone.now()
        
        if not self.is_active:
            return False
        
        if self.valid_from > now:
            return False
        
        if self.valid_until and self.valid_until < now:
            return False
        
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
        
        return True


class CouponUsage(models.Model):
    """Track individual coupon redemptions"""
    
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.PROTECT,
        related_name='usages'
    )
    
    customer_id = models.IntegerField(
        _('customer ID'),
        db_index=True,
        help_text=_('Customer user ID from auth-service')
    )
    
    order_id = models.IntegerField(
        _('order ID'),
        db_index=True,
        help_text=_('Order ID from order-service')
    )
    
    discount_amount = models.DecimalField(
        _('discount amount'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Actual discount applied to this order')
    )
    
    created_at = models.DateTimeField(_('used at'), auto_now_add=True)
    
    class Meta:
        db_table = 'coupon_usages'
        verbose_name = _('coupon usage')
        verbose_name_plural = _('coupon usages')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['coupon', '-created_at']),
            models.Index(fields=['customer_id', '-created_at']),
            models.Index(fields=['order_id']),
        ]
    
    def __str__(self):
        return f'Customer #{self.customer_id} used {self.coupon.code} on Order #{self.order_id}'
