"""
Admin Views for ALL Databases (Unified View)
Connects to auth_db, product_db, order_db, and admin_db
"""

from sqladmin import ModelView
import sys
import os

# Add shared models to path
shared_path = os.path.join(os.path.dirname(__file__), '../../shared')
if not os.path.exists(shared_path):
    shared_path = '/app/services/shared'
sys.path.insert(0, shared_path)

# Import admin_db models
from models_admin import Notification, Message, AuditLog, SystemSetting

# Import shared models (these will be used with different engines)
from models import (
    User, Category, Brand, Product, ProductImage, Order, OrderItem,
    Payment, Address, Review, Cart, CartItem, Wishlist, Coupon
)


# ==========================================
# ADMIN DB MODELS (admin_db)
# ==========================================

class NotificationAdmin(ModelView, model=Notification):
    column_list = [
        Notification.id, Notification.user_id, Notification.type,
        Notification.title, Notification.is_read, Notification.created_at
    ]
    column_searchable_list = [Notification.title, Notification.message]
    name = "Notification"
    name_plural = "Notifications"
    icon = "fa-solid fa-bell"


class MessageAdmin(ModelView, model=Message):
    column_list = [
        Message.id, Message.sender_id, Message.receiver_id,
        Message.subject, Message.is_read, Message.created_at
    ]
    column_searchable_list = [Message.subject, Message.message]
    name = "Message"
    name_plural = "Messages"
    icon = "fa-solid fa-envelope"


class AuditLogAdmin(ModelView, model=AuditLog):
    column_list = [
        AuditLog.id, AuditLog.admin_user_id, AuditLog.action,
        AuditLog.entity_type, AuditLog.entity_id, AuditLog.created_at
    ]
    can_create = False
    can_edit = False
    can_delete = False
    name = "Audit Log"
    name_plural = "Audit Logs"
    icon = "fa-solid fa-file-alt"


class SystemSettingAdmin(ModelView, model=SystemSetting):
    column_list = [
        SystemSetting.id, SystemSetting.key, SystemSetting.value,
        SystemSetting.description, SystemSetting.updated_by, SystemSetting.updated_at
    ]
    column_searchable_list = [SystemSetting.key, SystemSetting.description]
    name = "System Setting"
    name_plural = "System Settings"
    icon = "fa-solid fa-cog"


# ==========================================
# AUTH DB MODELS (auth_db)
# ==========================================

class UserAdmin(ModelView, model=User):
    column_list = [
        User.id, User.email, User.first_name, User.last_name,
        User.role, User.is_verified, User.is_active, User.created_at
    ]
    column_searchable_list = [User.email, User.first_name, User.last_name]
    column_sortable_list = [User.id, User.email, User.created_at]
    form_excluded_columns = [User.password_hash, User.created_at, User.updated_at]
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"
    column_details_exclude_list = [User.password_hash]


class AddressAdmin(ModelView, model=Address):
    column_list = [
        Address.id, Address.user_id, Address.address_type,
        Address.city, Address.country, Address.is_default, Address.created_at
    ]
    column_searchable_list = [Address.city, Address.country, Address.postal_code]
    name = "Address"
    name_plural = "Addresses"
    icon = "fa-solid fa-map-marker-alt"


# ==========================================
# PRODUCT DB MODELS (product_db)
# ==========================================

class CategoryAdmin(ModelView, model=Category):
    column_list = [
        Category.id, Category.name, Category.slug,
        Category.parent_id, Category.is_active, Category.position
    ]
    column_searchable_list = [Category.name, Category.slug]
    name = "Category"
    name_plural = "Categories"
    icon = "fa-solid fa-folder"


class ProductAdmin(ModelView, model=Product):
    column_list = [
        Product.id, Product.title, Product.price, Product.quantity,
        Product.status, Product.approval_status, Product.vendor_id, Product.created_at
    ]
    column_searchable_list = [Product.title, Product.sku]
    column_sortable_list = [Product.id, Product.title, Product.price, Product.created_at]
    name = "Product"
    name_plural = "Products"
    icon = "fa-solid fa-box"


class ProductImageAdmin(ModelView, model=ProductImage):
    column_list = [
        ProductImage.id, ProductImage.product_id,
        ProductImage.image_url, ProductImage.position, ProductImage.created_at
    ]
    name = "Product Image"
    name_plural = "Product Images"
    icon = "fa-solid fa-image"


class ReviewAdmin(ModelView, model=Review):
    column_list = [
        Review.id, Review.product_id, Review.user_id,
        Review.rating, Review.title, Review.is_verified_purchase, Review.created_at
    ]
    column_searchable_list = [Review.title, Review.comment]
    name = "Review"
    name_plural = "Reviews"
    icon = "fa-solid fa-star"


class CartItemAdmin(ModelView, model=CartItem):
    column_list = [
        CartItem.id, CartItem.cart_id, CartItem.product_id, CartItem.variant_id,
        CartItem.quantity, CartItem.unit_price, CartItem.created_at
    ]
    name = "Cart Item"
    name_plural = "Cart Items"
    icon = "fa-solid fa-shopping-cart"


class WishlistAdmin(ModelView, model=Wishlist):
    column_list = [
        Wishlist.id, Wishlist.user_id, Wishlist.product_id, Wishlist.created_at
    ]
    name = "Wishlist"
    name_plural = "Wishlist Items"
    icon = "fa-solid fa-heart"


class CouponAdmin(ModelView, model=Coupon):
    column_list = [
        Coupon.id, Coupon.code, Coupon.discount_type, Coupon.discount_value,
        Coupon.is_active, Coupon.valid_until, Coupon.created_at
    ]
    column_searchable_list = [Coupon.code]
    name = "Coupon"
    name_plural = "Coupons"
    icon = "fa-solid fa-ticket"


# ==========================================
# ORDER DB MODELS (order_db)
# ==========================================

class OrderAdmin(ModelView, model=Order):
    column_list = [
        Order.id, Order.order_number, Order.buyer_id, Order.status,
        Order.payment_status, Order.total, Order.created_at
    ]
    column_searchable_list = [Order.order_number]
    column_sortable_list = [Order.id, Order.created_at, Order.total]
    name = "Order"
    name_plural = "Orders"
    icon = "fa-solid fa-shopping-bag"


class OrderItemAdmin(ModelView, model=OrderItem):
    column_list = [
        OrderItem.id, OrderItem.order_id, OrderItem.product_id,
        OrderItem.quantity, OrderItem.price, OrderItem.total, OrderItem.created_at
    ]
    name = "Order Item"
    name_plural = "Order Items"
    icon = "fa-solid fa-list"


class PaymentAdmin(ModelView, model=Payment):
    column_list = [
        Payment.id, Payment.order_id, Payment.amount,
        Payment.status, Payment.payment_method, Payment.created_at
    ]
    column_searchable_list = [Payment.stripe_payment_id]
    name = "Payment"
    name_plural = "Payments"
    icon = "fa-solid fa-credit-card"


def register_all_admin_views(admin_instance, engines_dict):
    """
    Register admin views for all databases
    
    Args:
        admin_instance: SQLAdmin Admin instance
        engines_dict: Dictionary with keys 'auth', 'product', 'order', 'admin'
                     containing SQLAlchemy engines for each database
    """
    # Admin DB views (use admin engine)
    admin_instance.add_view(NotificationAdmin)
    admin_instance.add_view(MessageAdmin)
    admin_instance.add_view(AuditLogAdmin)
    admin_instance.add_view(SystemSettingAdmin)
    
    # Auth DB views (use auth engine)
    # Note: SQLAdmin doesn't support multiple engines directly
    # We'll register them but they'll use the default engine
    # For proper multi-DB support, we'd need separate Admin instances
    admin_instance.add_view(UserAdmin)
    admin_instance.add_view(AddressAdmin)
    
    # Product DB views
    admin_instance.add_view(CategoryAdmin)
    admin_instance.add_view(ProductAdmin)
    admin_instance.add_view(ProductImageAdmin)
    admin_instance.add_view(ReviewAdmin)
    admin_instance.add_view(CartItemAdmin)
    admin_instance.add_view(WishlistAdmin)
    admin_instance.add_view(CouponAdmin)
    
    # Order DB views
    admin_instance.add_view(OrderAdmin)
    admin_instance.add_view(OrderItemAdmin)
    admin_instance.add_view(PaymentAdmin)
    
    print("✅ Registered admin views for ALL databases:")
    print("   📊 Admin DB: Notifications, Messages, Audit Logs, System Settings")
    print("   👥 Auth DB: Users, Addresses")
    print("   📦 Product DB: Categories, Products, Product Images, Reviews, Cart Items, Wishlist, Coupons")
    print("   🛒 Order DB: Orders, Order Items, Payments")
    print("")
    print("⚠️  Note: All views use the admin_db connection.")
    print("   For proper multi-DB support, consider using Foreign Data Wrappers (FDW)")

