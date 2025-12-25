"""
SQLAlchemy Models for E-Commerce Database
"""

from sqlalchemy import Column, Integer, String, Text, DECIMAL, Boolean, TIMESTAMP, ForeignKey, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    avatar_url = Column(String(500))
    role = Column(String(20), default='user')
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    products = relationship("Product", back_populates="vendor", foreign_keys="Product.vendor_id")
    orders = relationship("Order", back_populates="buyer")
    reviews = relationship("Review", back_populates="user")
    addresses = relationship("Address", back_populates="user")
    wishlist = relationship("Wishlist", back_populates="user")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")
    notifications = relationship("Notification", back_populates="user")
    
    def __repr__(self):
        return f"{self.email} ({self.first_name} {self.last_name})"


class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey('categories.id'))
    image_url = Column(String(500))
    position = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    products = relationship("Product", back_populates="category")
    parent = relationship("Category", remote_side=[id], backref="children")
    
    def __repr__(self):
        return f"{self.name}"


class Brand(Base):
    __tablename__ = 'brands'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    logo = Column(String(100))
    website = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    products = relationship("Product", back_populates="brand")
    
    def __repr__(self):
        return f"{self.name}"


class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    vendor_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'))
    brand_id = Column(Integer, ForeignKey('brands.id'))
    title = Column(String(255), nullable=False)
    slug = Column(String(550))
    description = Column(Text)
    short_description = Column(Text)
    price = Column(DECIMAL(10, 2), nullable=False)
    compare_at_price = Column(DECIMAL(10, 2))
    cost_per_item = Column(DECIMAL(10, 2))
    quantity = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=5)
    track_inventory = Column(Boolean, default=True)
    allow_backorders = Column(Boolean, default=False)
    sku = Column(String(100))
    barcode = Column(String(100))
    condition = Column(String(20))
    status = Column(String(20), default='draft')
    approval_status = Column(String(20), default='pending')
    rejection_reason = Column(Text)
    weight = Column(DECIMAL(10, 2))
    length = Column(DECIMAL(10, 2))
    width = Column(DECIMAL(10, 2))
    height = Column(DECIMAL(10, 2))
    meta_title = Column(String(255))
    meta_description = Column(Text)
    meta_keywords = Column(String(500))
    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)
    views_count = Column(Integer, default=0)
    sales_count = Column(Integer, default=0)
    favorites_count = Column(Integer, default=0)
    published_at = Column(TIMESTAMP)
    approved_at = Column(TIMESTAMP)
    approved_by_id = Column(Integer, ForeignKey('users.id'))
    submitted_for_approval_at = Column(TIMESTAMP)
    deleted_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    vendor = relationship("User", back_populates="products", foreign_keys=[vendor_id])
    category = relationship("Category", back_populates="products")
    brand = relationship("Brand", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")
    reviews = relationship("Review", back_populates="product")
    cart_items = relationship("CartItem", back_populates="product")
    wishlist = relationship("Wishlist", back_populates="product")
    
    def __repr__(self):
        return f"{self.title} (${self.price})"


class ProductImage(Base):
    __tablename__ = 'product_images'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    image_url = Column(String(500), nullable=False)
    alt_text = Column(String(255))
    position = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="images")
    
    def __repr__(self):
        return f"Image {self.position} for Product #{self.product_id}"


class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String(50), unique=True, nullable=False)
    buyer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(String(30), default='pending')
    payment_status = Column(String(20), default='pending')
    payment_method = Column(String(50))
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    shipping_cost = Column(DECIMAL(10, 2), default=0)
    tax = Column(DECIMAL(10, 2), default=0)
    discount = Column(DECIMAL(10, 2), default=0)
    total = Column(DECIMAL(10, 2), nullable=False)
    shipping_address_id = Column(Integer, ForeignKey('addresses.id'))
    billing_address_id = Column(Integer, ForeignKey('addresses.id'))
    tracking_number = Column(String(100))
    carrier = Column(String(50))
    notes = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    buyer = relationship("User", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="order", uselist=False)
    shipping_address = relationship("Address", foreign_keys=[shipping_address_id])
    billing_address = relationship("Address", foreign_keys=[billing_address_id])
    
    def __repr__(self):
        return f"Order {self.order_number} (${self.total})"


class OrderItem(Base):
    __tablename__ = 'order_items'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    vendor_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    total = Column(DECIMAL(10, 2), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")
    vendor = relationship("User", foreign_keys=[vendor_id])
    
    def __repr__(self):
        return f"{self.title} x{self.quantity}"


class Payment(Base):
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    stripe_payment_id = Column(String(255))
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), default='USD')
    status = Column(String(20))
    payment_method = Column(String(50))
    error_message = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="payment")
    
    def __repr__(self):
        return f"Payment ${self.amount} ({self.status})"


class Address(Base):
    __tablename__ = 'addresses'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    address_type = Column(String(20), nullable=False)  # 'shipping' or 'billing'
    first_name = Column(String(100))
    last_name = Column(String(100))
    company = Column(String(100))
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255))
    city = Column(String(100), nullable=False)
    state = Column(String(100))
    postal_code = Column(String(20), nullable=False)
    country = Column(String(100), nullable=False)
    phone = Column(String(20))
    is_default = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="addresses")
    
    def __repr__(self):
        return f"{self.address_line1}, {self.city}, {self.country}"


class Review(Base):
    __tablename__ = 'reviews'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id'))
    rating = Column(Integer, nullable=False)
    title = Column(String(255))
    comment = Column(Text)
    is_verified_purchase = Column(Boolean, default=False)
    helpful_count = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating'),
    )
    
    # Relationships
    product = relationship("Product", back_populates="reviews")
    user = relationship("User", back_populates="reviews")
    
    def __repr__(self):
        return f"{self.rating}★ Review by User #{self.user_id}"


class Cart(Base):
    __tablename__ = 'carts'
    
    customer_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    items = relationship("CartItem", back_populates="cart")
    
    def __repr__(self):
        return f"Cart for Customer #{self.customer_id}"


class CartItem(Base):
    __tablename__ = 'cart_items'
    
    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey('carts.customer_id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    variant_id = Column(Integer, ForeignKey('product_variants.id'))
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(DECIMAL(12, 2), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product", back_populates="cart_items")
    
    def __repr__(self):
        return f"Cart: Product #{self.product_id} x{self.quantity}"


class Wishlist(Base):
    __tablename__ = 'wishlist'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="wishlist")
    product = relationship("Product", back_populates="wishlist")
    
    def __repr__(self):
        return f"Wishlist: Product #{self.product_id}"


class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    receiver_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    subject = Column(String(255))
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    parent_message_id = Column(Integer, ForeignKey('messages.id'))
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")
    
    def __repr__(self):
        return f"{self.subject or 'No Subject'}"


class Coupon(Base):
    __tablename__ = 'coupons'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255))
    description = Column(Text)
    discount_type = Column(String(20), nullable=False)  # 'percentage' or 'fixed'
    discount_value = Column(DECIMAL(10, 2), nullable=False)
    min_purchase_amount = Column(DECIMAL(10, 2))
    max_discount_amount = Column(DECIMAL(10, 2))
    usage_limit = Column(Integer)
    used_count = Column(Integer, default=0)
    max_uses_per_customer = Column(Integer, default=1)
    current_uses = Column(Integer, default=0)
    valid_from = Column(TIMESTAMP)
    valid_until = Column(TIMESTAMP)
    is_active = Column(Boolean, default=True)
    created_by_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    def __repr__(self):
        return f"{self.code} ({self.discount_value} {self.discount_type})"


class Notification(Base):
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    link = Column(String(500))
    is_read = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    
    def __repr__(self):
        return f"{self.title}"
