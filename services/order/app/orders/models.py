from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal

# Note: In microservices architecture, we use IDs (IntegerField) instead of ForeignKey
# to reference entities in other services (auth-service, product-service)


class OrderStatus(models.TextChoices):
    """Order lifecycle statuses"""
    PENDING = 'PENDING', _('Pending Payment')
    PAID = 'PAID', _('Paid')
    PROCESSING = 'PROCESSING', _('Processing')
    SHIPPED = 'SHIPPED', _('Shipped')
    DELIVERED = 'DELIVERED', _('Delivered')
    CANCELLED = 'CANCELLED', _('Cancelled')
    REFUNDED = 'REFUNDED', _('Refunded')
    FAILED = 'FAILED', _('Payment Failed')


class Order(models.Model):
    """
    Main order model.
    Represents a complete purchase by a customer.
    Can contain items from multiple vendors.
    """
    
    # Order Identification
    order_number = models.CharField(
        _('order number'),
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_('Unique order identifier shown to customer')
    )
    
    # Customer Information (user_id from auth-service)
    customer_id = models.IntegerField(
        _('customer ID'),
        db_index=True,
        help_text=_('Customer user ID from auth-service')
    )
    
    # Addresses (address_id from auth-service, stored as snapshot)
    shipping_address_id = models.IntegerField(
        _('shipping address ID'),
        help_text=_('Shipping address ID from auth-service (snapshot)')
    )
    
    billing_address_id = models.IntegerField(
        _('billing address ID'),
        help_text=_('Billing address ID from auth-service (snapshot)')
    )
    
    # Order Status
    status = models.CharField(
        _('order status'),
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True
    )
    
    # Financial Information
    subtotal = models.DecimalField(
        _('subtotal'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('Sum of all item prices')
    )
    
    tax_amount = models.DecimalField(
        _('tax amount'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    shipping_cost = models.DecimalField(
        _('shipping cost'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    discount_amount = models.DecimalField(
        _('discount amount'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('Total discount applied (coupons, promotions)')
    )
    
    total = models.DecimalField(
        _('total amount'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Final amount to be paid')
    )
    
    currency = models.CharField(
        _('currency'),
        max_length=3,
        default='USD',
        help_text=_('ISO 4217 currency code')
    )
    
    # Coupon/Discount
    coupon_code = models.CharField(
        _('coupon code'),
        max_length=50,
        blank=True,
        help_text=_('Applied coupon code')
    )
    
    # Customer Notes
    customer_note = models.TextField(
        _('customer note'),
        blank=True,
        help_text=_('Special instructions or comments from customer')
    )
    
    # Admin Notes
    admin_note = models.TextField(
        _('admin note'),
        blank=True,
        help_text=_('Internal notes (not visible to customer)')
    )
    
    # IP & User Agent (for fraud detection)
    ip_address = models.GenericIPAddressField(
        _('IP address'),
        null=True,
        blank=True,
        help_text=_('Customer IP address when order was placed')
    )
    
    user_agent = models.TextField(
        _('user agent'),
        blank=True,
        help_text=_('Customer browser user agent')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    paid_at = models.DateTimeField(_('paid at'), null=True, blank=True)
    shipped_at = models.DateTimeField(_('shipped at'), null=True, blank=True)
    delivered_at = models.DateTimeField(_('delivered at'), null=True, blank=True)
    cancelled_at = models.DateTimeField(_('cancelled at'), null=True, blank=True)
    
    class Meta:
        db_table = 'orders'
        verbose_name = _('order')
        verbose_name_plural = _('orders')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer_id', 'status']),
            models.Index(fields=['order_number']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f'Order #{self.order_number} - Customer #{self.customer_id}'
    
    @property
    def is_paid(self):
        """Check if order is paid"""
        return self.status not in [OrderStatus.PENDING, OrderStatus.FAILED]
    
    @property
    def can_be_cancelled(self):
        """Check if order can be cancelled"""
        return self.status in [OrderStatus.PENDING, OrderStatus.PAID, OrderStatus.PROCESSING]
    
    def calculate_total(self):
        """Calculate and return total amount"""
        return self.subtotal + self.tax_amount + self.shipping_cost - self.discount_amount


class OrderItem(models.Model):
    """
    Individual items in an order.
    Links to vendor for commission calculation and order splitting.
    """
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    # Vendor (vendor_id from auth-service)
    vendor_id = models.IntegerField(
        _('vendor ID'),
        db_index=True,
        help_text=_('Vendor user ID from auth-service')
    )
    
    # Product Information (product_id from product-service, snapshot at time of purchase)
    product_id = models.IntegerField(
        _('product ID'),
        db_index=True,
        help_text=_('Product ID from product-service')
    )
    
    variant_id = models.IntegerField(
        _('variant ID'),
        null=True,
        blank=True,
        db_index=True,
        help_text=_('Product variant ID from product-service (if applicable)')
    )
    
    # Snapshot data (preserve order details even if product changes)
    product_name = models.CharField(_('product name'), max_length=500)
    product_sku = models.CharField(_('SKU'), max_length=100)
    variant_name = models.CharField(_('variant name'), max_length=255, blank=True)
    
    # Pricing (at time of purchase)
    unit_price = models.DecimalField(
        _('unit price'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Price per unit at time of purchase')
    )
    
    quantity = models.PositiveIntegerField(
        _('quantity'),
        validators=[MinValueValidator(1)]
    )
    
    subtotal = models.DecimalField(
        _('subtotal'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('unit_price × quantity')
    )
    
    tax_amount = models.DecimalField(
        _('tax amount'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    discount_amount = models.DecimalField(
        _('discount amount'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    total = models.DecimalField(
        _('total'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Final line item total')
    )
    
    # Vendor Commission
    commission_rate = models.DecimalField(
        _('commission rate'),
        max_digits=5,
        decimal_places=2,
        help_text=_('Platform commission percentage at time of order')
    )
    
    commission_amount = models.DecimalField(
        _('commission amount'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Platform commission in currency')
    )
    
    vendor_payout = models.DecimalField(
        _('vendor payout'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Amount to be paid to vendor (total - commission)')
    )
    
    # Fulfillment Status (per item, not per order)
    is_shipped = models.BooleanField(_('shipped'), default=False)
    is_delivered = models.BooleanField(_('delivered'), default=False)
    is_cancelled = models.BooleanField(_('cancelled'), default=False)
    
    shipped_at = models.DateTimeField(_('shipped at'), null=True, blank=True)
    delivered_at = models.DateTimeField(_('delivered at'), null=True, blank=True)
    cancelled_at = models.DateTimeField(_('cancelled at'), null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'order_items'
        verbose_name = _('order item')
        verbose_name_plural = _('order items')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['vendor_id', 'is_shipped']),
            models.Index(fields=['product_id']),
        ]
    
    def __str__(self):
        return f'{self.product_name} x{self.quantity} - Order #{self.order.order_number}'
    
    def save(self, *args, **kwargs):
        # Auto-calculate subtotal if not set
        if not self.subtotal:
            self.subtotal = self.unit_price * self.quantity
        
        # Auto-calculate vendor payout
        if not self.vendor_payout:
            self.vendor_payout = self.total - self.commission_amount
        
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    """
    Tracks all status changes for an order.
    Provides audit trail and order timeline.
    """
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    
    old_status = models.CharField(
        _('old status'),
        max_length=20,
        choices=OrderStatus.choices,
        blank=True
    )
    
    new_status = models.CharField(
        _('new status'),
        max_length=20,
        choices=OrderStatus.choices
    )
    
    changed_by_id = models.IntegerField(
        _('changed by user ID'),
        null=True,
        blank=True,
        db_index=True,
        help_text=_('User ID from auth-service who made the change')
    )
    
    comment = models.TextField(
        _('comment'),
        blank=True,
        help_text=_('Additional notes about this status change')
    )
    
    notified_customer = models.BooleanField(
        _('customer notified'),
        default=False,
        help_text=_('Was customer notified about this change?')
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        db_table = 'order_status_history'
        verbose_name = _('order status history')
        verbose_name_plural = _('order status histories')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['order', 'created_at']),
        ]
    
    def __str__(self):
        return f'Order #{self.order.order_number}: {self.old_status} → {self.new_status}'


class Cart(models.Model):
    """
    Shopping cart for customers.
    Persists across sessions.
    """
    
    customer_id = models.IntegerField(
        _('customer ID'),
        primary_key=True,
        db_index=True,
        help_text=_('Customer user ID from auth-service')
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'carts'
        verbose_name = _('shopping cart')
        verbose_name_plural = _('shopping carts')
    
    def __str__(self):
        return f'Cart - Customer #{self.customer_id}'
    
    @property
    def total_items(self):
        """Get total number of items in cart"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def subtotal(self):
        """Calculate cart subtotal"""
        return sum(item.subtotal for item in self.items.all())


class CartItem(models.Model):
    """Individual items in a shopping cart"""
    
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    product_id = models.IntegerField(
        _('product ID'),
        db_index=True,
        help_text=_('Product ID from product-service')
    )
    
    variant_id = models.IntegerField(
        _('variant ID'),
        null=True,
        blank=True,
        db_index=True,
        help_text=_('Product variant ID from product-service (if applicable)')
    )
    
    quantity = models.PositiveIntegerField(
        _('quantity'),
        default=1,
        validators=[MinValueValidator(1)]
    )
    
    # Cache the price at time of adding to cart
    unit_price = models.DecimalField(
        _('unit price'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    created_at = models.DateTimeField(_('added at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'cart_items'
        verbose_name = _('cart item')
        verbose_name_plural = _('cart items')
        ordering = ['created_at']
        unique_together = [['cart', 'product_id', 'variant_id']]
        indexes = [
            models.Index(fields=['cart']),
        ]
    
    def __str__(self):
        variant_text = f' (Variant #{self.variant_id})' if self.variant_id else ''
        return f'Product #{self.product_id}{variant_text} x{self.quantity}'
    
    @property
    def subtotal(self):
        """Calculate line item subtotal"""
        return self.unit_price * self.quantity
    
    def save(self, *args, **kwargs):
        # Note: In microservices, price should be fetched from product-service API
        # For now, unit_price must be provided when creating cart item
        super().save(*args, **kwargs)


class Refund(models.Model):
    """
    Refund requests and processing.
    Can be full or partial refunds.
    """
    
    class RefundStatus(models.TextChoices):
        REQUESTED = 'REQUESTED', _('Requested')
        PROCESSING = 'PROCESSING', _('Processing')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')
        COMPLETED = 'COMPLETED', _('Completed')
    
    class RefundReason(models.TextChoices):
        DAMAGED = 'DAMAGED', _('Product Damaged')
        DEFECTIVE = 'DEFECTIVE', _('Product Defective')
        WRONG_ITEM = 'WRONG_ITEM', _('Wrong Item Received')
        NOT_AS_DESCRIBED = 'NOT_AS_DESCRIBED', _('Not As Described')
        CHANGED_MIND = 'CHANGED_MIND', _('Changed Mind')
        OTHER = 'OTHER', _('Other')
    
    # Unique refund ID
    refund_number = models.CharField(
        _('refund number'),
        max_length=50,
        unique=True,
        db_index=True
    )
    
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name='refunds'
    )
    
    # Can refund specific items or entire order
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='refunds',
        help_text=_('Specific item to refund (leave blank for full order refund)')
    )
    
    customer_id = models.IntegerField(
        _('customer ID'),
        db_index=True,
        help_text=_('Customer user ID from auth-service')
    )
    
    status = models.CharField(
        _('refund status'),
        max_length=20,
        choices=RefundStatus.choices,
        default=RefundStatus.REQUESTED,
        db_index=True
    )
    
    reason = models.CharField(
        _('refund reason'),
        max_length=20,
        choices=RefundReason.choices
    )
    
    description = models.TextField(
        _('description'),
        help_text=_('Customer explanation for refund request')
    )
    
    refund_amount = models.DecimalField(
        _('refund amount'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Admin response
    admin_note = models.TextField(_('admin note'), blank=True)
    processed_by_id = models.IntegerField(
        _('processed by user ID'),
        null=True,
        blank=True,
        db_index=True,
        help_text=_('Admin user ID from auth-service who processed this refund')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('requested at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    processed_at = models.DateTimeField(_('processed at'), null=True, blank=True)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    
    class Meta:
        db_table = 'refunds'
        verbose_name = _('refund')
        verbose_name_plural = _('refunds')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order', 'status']),
            models.Index(fields=['customer_id', '-created_at']),
            models.Index(fields=['refund_number']),
        ]
    
    def __str__(self):
        return f'Refund #{self.refund_number} - Order #{self.order.order_number}'
