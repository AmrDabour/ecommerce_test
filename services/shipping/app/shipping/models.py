from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal

# Note: In microservices architecture, we use IDs instead of ForeignKey
# to reference entities in other services


class ShippingMethod(models.Model):
    """
    Available shipping methods (e.g., Standard, Express, Overnight).
    Admin configures rates and delivery estimates.
    """
    
    name = models.CharField(
        _('shipping method name'),
        max_length=255,
        unique=True,
        help_text=_('e.g., "Standard Shipping", "Express Delivery"')
    )
    
    description = models.TextField(_('description'), blank=True)
    
    # Pricing
    base_cost = models.DecimalField(
        _('base cost'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('Base shipping cost')
    )
    
    cost_per_kg = models.DecimalField(
        _('cost per kg'),
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('Additional cost per kilogram')
    )
    
    # Free shipping threshold
    free_shipping_threshold = models.DecimalField(
        _('free shipping threshold'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Order total for free shipping (null = no free shipping)')
    )
    
    # Delivery Time
    min_delivery_days = models.PositiveIntegerField(
        _('minimum delivery days'),
        help_text=_('Estimated minimum days for delivery')
    )
    
    max_delivery_days = models.PositiveIntegerField(
        _('maximum delivery days'),
        help_text=_('Estimated maximum days for delivery')
    )
    
    # Availability
    is_active = models.BooleanField(_('active'), default=True)
    is_international = models.BooleanField(
        _('international shipping'),
        default=True,
        help_text=_('Available for international orders?')
    )
    
    # Display
    display_order = models.PositiveIntegerField(_('display order'), default=0)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'shipping_methods'
        verbose_name = _('shipping method')
        verbose_name_plural = _('shipping methods')
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name
    
    def calculate_cost(self, order_total, weight_kg=0):
        """Calculate shipping cost based on order total and weight"""
        # Check if eligible for free shipping
        if self.free_shipping_threshold and order_total >= self.free_shipping_threshold:
            return Decimal('0.00')
        
        # Base cost + weight-based cost
        cost = self.base_cost + (self.cost_per_kg * Decimal(str(weight_kg)))
        return cost


class ShippingZone(models.Model):
    """
    Shipping zones for different countries/regions.
    Allows different rates for different geographic areas.
    """
    
    name = models.CharField(
        _('zone name'),
        max_length=255,
        unique=True,
        help_text=_('e.g., "North America", "European Union"')
    )
    
    description = models.TextField(_('description'), blank=True)
    
    # Countries in this zone (comma-separated ISO codes)
    countries = models.TextField(
        _('country codes'),
        help_text=_('Comma-separated ISO 3166-1 alpha-2 country codes (e.g., US,CA,MX)')
    )
    
    # Pricing multiplier
    price_multiplier = models.DecimalField(
        _('price multiplier'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Multiply shipping cost by this value (e.g., 1.5 = +50%)')
    )
    
    # Additional flat fee
    additional_fee = models.DecimalField(
        _('additional fee'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('Flat fee added to shipping cost')
    )
    
    is_active = models.BooleanField(_('active'), default=True)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'shipping_zones'
        verbose_name = _('shipping zone')
        verbose_name_plural = _('shipping zones')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_countries_list(self):
        """Return list of country codes"""
        return [code.strip().upper() for code in self.countries.split(',') if code.strip()]
    
    def includes_country(self, country_code):
        """Check if country is in this zone"""
        return country_code.upper() in self.get_countries_list()


class Shipment(models.Model):
    """
    Individual shipments for orders.
    An order can have multiple shipments (e.g., items from different vendors).
    """
    
    class ShipmentStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        PROCESSING = 'PROCESSING', _('Processing')
        READY_TO_SHIP = 'READY_TO_SHIP', _('Ready to Ship')
        SHIPPED = 'SHIPPED', _('Shipped')
        IN_TRANSIT = 'IN_TRANSIT', _('In Transit')
        OUT_FOR_DELIVERY = 'OUT_FOR_DELIVERY', _('Out for Delivery')
        DELIVERED = 'DELIVERED', _('Delivered')
        FAILED_DELIVERY = 'FAILED_DELIVERY', _('Failed Delivery')
        RETURNED = 'RETURNED', _('Returned')
        CANCELLED = 'CANCELLED', _('Cancelled')
    
    # Shipment Identification
    tracking_number = models.CharField(
        _('tracking number'),
        max_length=255,
        unique=True,
        db_index=True,
        help_text=_('Unique tracking number from carrier')
    )
    
    # Relations (order_id from order-service, vendor_id from auth-service)
    order_id = models.IntegerField(
        _('order ID'),
        db_index=True,
        help_text=_('Order ID from order-service')
    )
    
    vendor_id = models.IntegerField(
        _('vendor ID'),
        null=True,
        blank=True,
        db_index=True,
        help_text=_('Vendor user ID from auth-service responsible for this shipment')
    )
    
    # Shipping Details
    shipping_method = models.ForeignKey(
        ShippingMethod,
        on_delete=models.PROTECT,
        related_name='shipments'
    )
    
    status = models.CharField(
        _('shipment status'),
        max_length=30,
        choices=ShipmentStatus.choices,
        default=ShipmentStatus.PENDING,
        db_index=True
    )
    
    # Carrier Information
    carrier_name = models.CharField(
        _('carrier name'),
        max_length=255,
        blank=True,
        help_text=_('e.g., DHL, FedEx, UPS')
    )
    
    carrier_service = models.CharField(
        _('carrier service'),
        max_length=255,
        blank=True,
        help_text=_('e.g., "FedEx International Priority"')
    )
    
    carrier_tracking_url = models.URLField(
        _('tracking URL'),
        blank=True,
        help_text=_('Full URL to track shipment on carrier website')
    )
    
    # Weight & Dimensions
    total_weight = models.DecimalField(
        _('total weight (kg)'),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    length = models.DecimalField(
        _('length (cm)'),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    width = models.DecimalField(
        _('width (cm)'),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    height = models.DecimalField(
        _('height (cm)'),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Costs
    shipping_cost = models.DecimalField(
        _('shipping cost'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('Actual shipping cost charged to customer')
    )
    
    carrier_cost = models.DecimalField(
        _('carrier cost'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Actual cost charged by carrier (for profit calculation)')
    )
    
    # Estimated Delivery
    estimated_delivery_date = models.DateTimeField(
        _('estimated delivery date'),
        null=True,
        blank=True
    )
    
    # Addresses (snapshot - preserved even if order addresses change)
    shipping_address_snapshot = models.TextField(
        _('shipping address'),
        help_text=_('Full formatted shipping address as text')
    )
    
    # Notes
    special_instructions = models.TextField(
        _('special instructions'),
        blank=True,
        help_text=_('Special handling instructions for carrier')
    )
    
    notes = models.TextField(
        _('internal notes'),
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    shipped_at = models.DateTimeField(_('shipped at'), null=True, blank=True)
    delivered_at = models.DateTimeField(_('delivered at'), null=True, blank=True)
    
    class Meta:
        db_table = 'shipments'
        verbose_name = _('shipment')
        verbose_name_plural = _('shipments')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_id', 'status']),
            models.Index(fields=['vendor_id', 'status']),
            models.Index(fields=['tracking_number']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f'Shipment {self.tracking_number} - Order #{self.order_id}'


class ShipmentItem(models.Model):
    """
    Individual items in a shipment.
    Links OrderItems to Shipments.
    """
    
    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    order_item_id = models.IntegerField(
        _('order item ID'),
        db_index=True,
        help_text=_('Order item ID from order-service')
    )
    
    quantity = models.PositiveIntegerField(
        _('quantity'),
        validators=[MinValueValidator(1)],
        help_text=_('Quantity of this item in shipment (can be partial)')
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        db_table = 'shipment_items'
        verbose_name = _('shipment item')
        verbose_name_plural = _('shipment items')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['shipment']),
            models.Index(fields=['order_item_id']),
        ]
    
    def __str__(self):
        return f'Order Item #{self.order_item_id} x{self.quantity} in {self.shipment.tracking_number}'


class ShipmentTracking(models.Model):
    """
    Shipment tracking events.
    Records shipment status changes and location updates.
    """
    
    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name='tracking_events'
    )
    
    status = models.CharField(
        _('status'),
        max_length=30,
        help_text=_('Status at this tracking point')
    )
    
    location = models.CharField(
        _('location'),
        max_length=500,
        blank=True,
        help_text=_('Current location of package')
    )
    
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Detailed status description from carrier')
    )
    
    event_time = models.DateTimeField(
        _('event time'),
        help_text=_('When this tracking event occurred')
    )
    
    # Carrier-specific data
    carrier_status_code = models.CharField(
        _('carrier status code'),
        max_length=100,
        blank=True
    )
    
    created_at = models.DateTimeField(_('recorded at'), auto_now_add=True)
    
    class Meta:
        db_table = 'shipment_tracking'
        verbose_name = _('shipment tracking event')
        verbose_name_plural = _('shipment tracking events')
        ordering = ['-event_time']
        indexes = [
            models.Index(fields=['shipment', '-event_time']),
        ]
    
    def __str__(self):
        return f'{self.shipment.tracking_number} - {self.status} at {self.event_time}'


class ShippingLabel(models.Model):
    """
    Shipping labels generated for shipments.
    Stores label files and related data.
    """
    
    shipment = models.OneToOneField(
        Shipment,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='label'
    )
    
    # Label Files
    label_file = models.FileField(
        _('label file'),
        upload_to='shipping_labels/%Y/%m/',
        help_text=_('PDF or image file of shipping label')
    )
    
    label_format = models.CharField(
        _('label format'),
        max_length=10,
        choices=[
            ('PDF', 'PDF'),
            ('PNG', 'PNG'),
            ('ZPL', 'ZPL'),  # Zebra Printer Language
        ],
        default='PDF'
    )
    
    # Label Data
    label_id = models.CharField(
        _('label ID'),
        max_length=255,
        blank=True,
        help_text=_('Carrier-provided label ID')
    )
    
    rate_id = models.CharField(
        _('rate ID'),
        max_length=255,
        blank=True,
        help_text=_('Rate ID from carrier API')
    )
    
    postage_cost = models.DecimalField(
        _('postage cost'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('Cost of postage/label')
    )
    
    # Barcode
    barcode = models.CharField(
        _('barcode'),
        max_length=255,
        blank=True
    )
    
    # Void status
    is_voided = models.BooleanField(
        _('voided'),
        default=False,
        help_text=_('Has this label been voided?')
    )
    
    voided_at = models.DateTimeField(_('voided at'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'shipping_labels'
        verbose_name = _('shipping label')
        verbose_name_plural = _('shipping labels')
    
    def __str__(self):
        return f'Label for {self.shipment.tracking_number}'


class ReturnRequest(models.Model):
    """
    Product return requests from customers.
    Separate from refunds - customer wants to return physical items.
    """
    
    class ReturnStatus(models.TextChoices):
        REQUESTED = 'REQUESTED', _('Requested')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')
        SHIPPED = 'SHIPPED', _('Shipped by Customer')
        RECEIVED = 'RECEIVED', _('Received by Vendor')
        INSPECTED = 'INSPECTED', _('Inspected')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')
    
    class ReturnReason(models.TextChoices):
        DEFECTIVE = 'DEFECTIVE', _('Defective/Damaged')
        WRONG_ITEM = 'WRONG_ITEM', _('Wrong Item')
        NOT_AS_DESCRIBED = 'NOT_AS_DESCRIBED', _('Not as Described')
        SIZE_ISSUE = 'SIZE_ISSUE', _('Size/Fit Issue')
        QUALITY_ISSUE = 'QUALITY_ISSUE', _('Quality Issue')
        CHANGED_MIND = 'CHANGED_MIND', _('Changed Mind')
        OTHER = 'OTHER', _('Other')
    
    # Return Identification
    return_number = models.CharField(
        _('return number'),
        max_length=50,
        unique=True,
        db_index=True
    )
    
    # Relations (order_id and order_item_id from order-service)
    order_id = models.IntegerField(
        _('order ID'),
        db_index=True,
        help_text=_('Order ID from order-service')
    )
    
    order_item_id = models.IntegerField(
        _('order item ID'),
        db_index=True,
        help_text=_('Order item ID from order-service (specific item being returned)')
    )
    
    customer_id = models.IntegerField(
        _('customer ID'),
        db_index=True,
        help_text=_('Customer user ID from auth-service')
    )
    
    vendor_id = models.IntegerField(
        _('vendor ID'),
        db_index=True,
        help_text=_('Vendor user ID from auth-service')
    )
    
    # Return Details
    status = models.CharField(
        _('return status'),
        max_length=20,
        choices=ReturnStatus.choices,
        default=ReturnStatus.REQUESTED,
        db_index=True
    )
    
    reason = models.CharField(
        _('return reason'),
        max_length=20,
        choices=ReturnReason.choices
    )
    
    description = models.TextField(
        _('description'),
        help_text=_('Customer explanation for return')
    )
    
    quantity = models.PositiveIntegerField(
        _('quantity to return'),
        validators=[MinValueValidator(1)]
    )
    
    # Images (if customer uploads photos of defects)
    image_1 = models.ImageField(
        _('image 1'),
        upload_to='returns/%Y/%m/',
        blank=True,
        null=True
    )
    
    image_2 = models.ImageField(
        _('image 2'),
        upload_to='returns/%Y/%m/',
        blank=True,
        null=True
    )
    
    image_3 = models.ImageField(
        _('image 3'),
        upload_to='returns/%Y/%m/',
        blank=True,
        null=True
    )
    
    # Return Shipping
    return_tracking_number = models.CharField(
        _('return tracking number'),
        max_length=255,
        blank=True,
        help_text=_('Tracking number for return shipment')
    )
    
    return_carrier = models.CharField(
        _('return carrier'),
        max_length=255,
        blank=True
    )
    
    return_label_provided = models.BooleanField(
        _('return label provided'),
        default=False,
        help_text=_('Did vendor/platform provide prepaid return label?')
    )
    
    # Resolution
    resolution_note = models.TextField(
        _('resolution note'),
        blank=True,
        help_text=_('Vendor/admin notes on resolution')
    )
    
    processed_by_id = models.IntegerField(
        _('processed by user ID'),
        null=True,
        blank=True,
        db_index=True,
        help_text=_('Vendor or admin user ID from auth-service who processed this')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('requested at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    approved_at = models.DateTimeField(_('approved at'), null=True, blank=True)
    received_at = models.DateTimeField(_('received at'), null=True, blank=True)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    
    class Meta:
        db_table = 'return_requests'
        verbose_name = _('return request')
        verbose_name_plural = _('return requests')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_id', 'status']),
            models.Index(fields=['customer_id', '-created_at']),
            models.Index(fields=['vendor_id', 'status']),
            models.Index(fields=['return_number']),
        ]
    
    def __str__(self):
        return f'Return #{self.return_number} - Order #{self.order_id}'
