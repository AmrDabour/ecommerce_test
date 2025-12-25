from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

# Note: In microservices architecture, we use user_id (IntegerField) instead of ForeignKey
# to reference users in the auth-service database


class ProductStatus(models.TextChoices):
    """Product approval workflow statuses"""
    PENDING = 'PENDING', _('Pending Approval')
    APPROVED = 'APPROVED', _('Approved')
    REJECTED = 'REJECTED', _('Rejected')
    DRAFT = 'DRAFT', _('Draft')
    OUT_OF_STOCK = 'OUT_OF_STOCK', _('Out of Stock')


class Category(models.Model):
    """
    Hierarchical product categories.
    Supports nested categories (e.g., Electronics > Smartphones > Android).
    """
    
    name = models.CharField(_('category name'), max_length=255, unique=True)
    slug = models.SlugField(_('slug'), max_length=255, unique=True, db_index=True)
    description = models.TextField(_('description'), blank=True)
    
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text=_('Parent category for nested structure')
    )
    
    image = models.ImageField(
        _('category image'),
        upload_to='categories/%Y/%m/',
        blank=True,
        null=True
    )
    
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Is this category visible to customers?')
    )
    
    display_order = models.PositiveIntegerField(
        _('display order'),
        default=0,
        help_text=_('Order in which categories are displayed')
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['parent', 'is_active']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        if self.parent:
            return f'{self.parent.name} > {self.name}'
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_full_path(self):
        """Return full category path (e.g., 'Electronics > Smartphones > Android')"""
        path = [self.name]
        parent = self.parent
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent
        return ' > '.join(path)


class Brand(models.Model):
    """Product brands/manufacturers"""
    
    name = models.CharField(_('brand name'), max_length=255, unique=True)
    slug = models.SlugField(_('slug'), max_length=255, unique=True, db_index=True)
    description = models.TextField(_('description'), blank=True)
    
    logo = models.ImageField(
        _('brand logo'),
        upload_to='brands/%Y/%m/',
        blank=True,
        null=True
    )
    
    website = models.URLField(_('website'), blank=True)
    
    is_active = models.BooleanField(_('active'), default=True)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'brands'
        verbose_name = _('brand')
        verbose_name_plural = _('brands')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    Core product model with admin approval workflow.
    Vendors create products, admins approve them.
    """
    
    # Ownership (user_id from auth-service, not ForeignKey)
    vendor_id = models.IntegerField(
        _('vendor ID'),
        db_index=True,
        help_text=_('Vendor user ID from auth-service')
    )
    
    # Basic Information
    name = models.CharField(_('product name'), max_length=500, db_index=True)
    slug = models.SlugField(_('slug'), max_length=550, unique=True, db_index=True)
    sku = models.CharField(
        _('SKU'),
        max_length=100,
        unique=True,
        db_index=True,
        help_text=_('Stock Keeping Unit - unique product identifier')
    )
    
    description = models.TextField(_('description'))
    short_description = models.TextField(
        _('short description'),
        max_length=500,
        blank=True,
        help_text=_('Brief product summary for listings')
    )
    
    # Classification
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        db_index=True
    )
    
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    
    # Pricing
    price = models.DecimalField(
        _('price'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Regular selling price')
    )
    
    compare_at_price = models.DecimalField(
        _('compare at price'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('Original price for showing discounts')
    )
    
    cost_price = models.DecimalField(
        _('cost price'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('Vendor cost - for margin calculation')
    )
    
    # Inventory
    stock_quantity = models.PositiveIntegerField(
        _('stock quantity'),
        default=0,
        help_text=_('Available quantity in stock')
    )
    
    low_stock_threshold = models.PositiveIntegerField(
        _('low stock threshold'),
        default=10,
        help_text=_('Alert when stock falls below this number')
    )
    
    track_inventory = models.BooleanField(
        _('track inventory'),
        default=True,
        help_text=_('Enable stock tracking for this product')
    )
    
    allow_backorders = models.BooleanField(
        _('allow backorders'),
        default=False,
        help_text=_('Allow purchases when out of stock')
    )
    
    # Physical Properties
    weight = models.DecimalField(
        _('weight (kg)'),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    length = models.DecimalField(
        _('length (cm)'),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    width = models.DecimalField(
        _('width (cm)'),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    height = models.DecimalField(
        _('height (cm)'),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Approval Workflow
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=ProductStatus.choices,
        default=ProductStatus.DRAFT,
        db_index=True
    )
    
    approved_by_id = models.IntegerField(
        _('approved by user ID'),
        null=True,
        blank=True,
        db_index=True,
        help_text=_('Admin user ID from auth-service who approved this product')
    )
    
    approved_at = models.DateTimeField(_('approved at'), null=True, blank=True)
    rejection_reason = models.TextField(_('rejection reason'), blank=True)
    submitted_for_approval_at = models.DateTimeField(
        _('submitted for approval at'),
        null=True,
        blank=True
    )
    
    # SEO & Marketing
    meta_title = models.CharField(_('meta title'), max_length=255, blank=True)
    meta_description = models.TextField(_('meta description'), max_length=500, blank=True)
    meta_keywords = models.CharField(_('meta keywords'), max_length=500, blank=True)
    
    # Visibility & Features
    is_featured = models.BooleanField(
        _('featured'),
        default=False,
        help_text=_('Display in featured product sections')
    )
    
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Is product active? (vendor can deactivate)')
    )
    
    # Statistics
    view_count = models.PositiveIntegerField(_('view count'), default=0)
    sales_count = models.PositiveIntegerField(_('sales count'), default=0)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    published_at = models.DateTimeField(_('published at'), null=True, blank=True)
    
    class Meta:
        db_table = 'products'
        verbose_name = _('product')
        verbose_name_plural = _('products')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vendor_id', 'status']),
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['category', 'status', 'is_active']),
            models.Index(fields=['slug']),
            models.Index(fields=['sku']),
            models.Index(fields=['is_featured', 'status']),
            models.Index(fields=['-sales_count']),
        ]
    
    def __str__(self):
        return f'{self.name} - Vendor #{self.vendor_id}'
    
    @property
    def is_approved(self):
        """Check if product is approved"""
        return self.status == ProductStatus.APPROVED
    
    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        if not self.track_inventory:
            return True
        return self.stock_quantity > 0 or self.allow_backorders
    
    @property
    def is_low_stock(self):
        """Check if product is low in stock"""
        if not self.track_inventory:
            return False
        return 0 < self.stock_quantity <= self.low_stock_threshold
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage if compare_at_price exists"""
        if self.compare_at_price and self.compare_at_price > self.price:
            return ((self.compare_at_price - self.price) / self.compare_at_price) * 100
        return 0
    
    def save(self, *args, **kwargs):
        # Auto-generate slug from name and SKU
        if not self.slug:
            base_slug = slugify(f'{self.name}-{self.sku}')
            self.slug = base_slug
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    """Product images - supports multiple images per product"""
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    
    image = models.ImageField(
        _('image'),
        upload_to='products/%Y/%m/',
        help_text=_('Product image')
    )
    
    alt_text = models.CharField(
        _('alt text'),
        max_length=255,
        blank=True,
        help_text=_('Alternative text for accessibility')
    )
    
    is_primary = models.BooleanField(
        _('primary image'),
        default=False,
        help_text=_('Main product image')
    )
    
    display_order = models.PositiveIntegerField(
        _('display order'),
        default=0
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        db_table = 'product_images'
        verbose_name = _('product image')
        verbose_name_plural = _('product images')
        ordering = ['display_order', 'created_at']
        indexes = [
            models.Index(fields=['product', 'is_primary']),
        ]
    
    def __str__(self):
        return f'{self.product.name} - Image {self.display_order}'


class ProductVariant(models.Model):
    """
    Product variants (e.g., Size: Small, Color: Red).
    Allows products to have different SKUs, prices, and stock per variant.
    """
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    
    name = models.CharField(
        _('variant name'),
        max_length=255,
        help_text=_('e.g., "Small / Red"')
    )
    
    sku = models.CharField(
        _('variant SKU'),
        max_length=100,
        unique=True,
        db_index=True
    )
    
    price = models.DecimalField(
        _('variant price'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('Override product price for this variant')
    )
    
    stock_quantity = models.PositiveIntegerField(
        _('stock quantity'),
        default=0
    )
    
    weight = models.DecimalField(
        _('weight (kg)'),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    image = models.ImageField(
        _('variant image'),
        upload_to='product_variants/%Y/%m/',
        blank=True,
        null=True,
        help_text=_('Specific image for this variant')
    )
    
    is_active = models.BooleanField(_('active'), default=True)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'product_variants'
        verbose_name = _('product variant')
        verbose_name_plural = _('product variants')
        ordering = ['name']
        indexes = [
            models.Index(fields=['product', 'is_active']),
            models.Index(fields=['sku']),
        ]
    
    def __str__(self):
        return f'{self.product.name} - {self.name}'
    
    @property
    def effective_price(self):
        """Return variant price if set, otherwise product price"""
        return self.price if self.price else self.product.price


class ProductAttribute(models.Model):
    """
    Product attributes/specifications (e.g., Material: Cotton, Warranty: 2 years).
    Flexible key-value pairs for product specifications.
    """
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='attributes'
    )
    
    name = models.CharField(
        _('attribute name'),
        max_length=255,
        help_text=_('e.g., "Material", "Color", "Warranty"')
    )
    
    value = models.CharField(
        _('attribute value'),
        max_length=500,
        help_text=_('e.g., "100% Cotton", "Red", "2 Years"')
    )
    
    display_order = models.PositiveIntegerField(_('display order'), default=0)
    
    class Meta:
        db_table = 'product_attributes'
        verbose_name = _('product attribute')
        verbose_name_plural = _('product attributes')
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['product']),
        ]
    
    def __str__(self):
        return f'{self.name}: {self.value}'


class ProductReview(models.Model):
    """Customer product reviews and ratings"""
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    
    customer_id = models.IntegerField(
        _('customer ID'),
        db_index=True,
        help_text=_('Customer user ID from auth-service')
    )
    
    rating = models.PositiveSmallIntegerField(
        _('rating'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Rating from 1 to 5 stars')
    )
    
    title = models.CharField(_('review title'), max_length=255, blank=True)
    comment = models.TextField(_('comment'), blank=True)
    
    is_verified_purchase = models.BooleanField(
        _('verified purchase'),
        default=False,
        help_text=_('Customer purchased this product')
    )
    
    is_approved = models.BooleanField(
        _('approved'),
        default=False,
        help_text=_('Review approved by admin')
    )
    
    helpful_count = models.PositiveIntegerField(
        _('helpful count'),
        default=0,
        help_text=_('Number of users who found this helpful')
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'product_reviews'
        verbose_name = _('product review')
        verbose_name_plural = _('product reviews')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'is_approved']),
            models.Index(fields=['customer_id']),
            models.Index(fields=['-helpful_count']),
        ]
        unique_together = [['product', 'customer_id']]  # One review per customer per product
    
    def __str__(self):
        return f'Customer #{self.customer_id} - {self.product.name} ({self.rating}★)'


class Wishlist(models.Model):
    """Customer wishlists for saving products"""
    
    customer_id = models.IntegerField(
        _('customer ID'),
        db_index=True,
        help_text=_('Customer user ID from auth-service')
    )
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='wishlisted_by'
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        db_table = 'wishlists'
        verbose_name = _('wishlist item')
        verbose_name_plural = _('wishlist items')
        ordering = ['-created_at']
        unique_together = [['customer_id', 'product']]
        indexes = [
            models.Index(fields=['customer_id', 'created_at']),
        ]
    
    def __str__(self):
        return f'Customer #{self.customer_id} - {self.product.name}'
