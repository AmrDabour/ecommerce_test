"""
Admin Views - SQLAdmin Model Views
All admin interface configurations
"""

from sqladmin import ModelView
from wtforms import PasswordField
from wtforms.validators import Optional
from passlib.context import CryptContext
import bcrypt
import sys
import os

# Add shared models to path
shared_path = os.path.join(os.path.dirname(__file__), '../../shared')
if not os.path.exists(shared_path):
    # Docker path
    shared_path = '/app/services/shared'
sys.path.insert(0, shared_path)

from models import (
    User, Category, Product, ProductImage, Order, OrderItem,
    Payment, Address, Review, CartItem, Wishlist, Message, 
    Coupon, Notification
)

# Fix for "error reading bcrypt version" warning
if not hasattr(bcrypt, "__about__"):
    class BcryptAbout:
        __version__ = getattr(bcrypt, "__version__", "4.0.0")
    bcrypt.__about__ = BcryptAbout

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.first_name, User.last_name, User.role, User.is_verified, User.is_active]
    column_searchable_list = [User.email, User.first_name, User.last_name]
    column_sortable_list = [User.id, User.email, User.created_at]
    form_excluded_columns = [User.password_hash, User.created_at, User.updated_at]
    
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"
    column_details_exclude_list = [User.password_hash]
    
    form_extra_fields = {
        'password': PasswordField('Password', validators=[Optional()])
    }
    
    async def on_model_change(self, data: dict, model, is_created: bool, request):
        """Hash password before saving"""
        if 'password' in data and data['password']:
            model.password_hash = pwd_context.hash(data['password'])
        elif is_created:
            model.password_hash = pwd_context.hash('changeme123')
        
        if 'password' in data:
            del data['password']
        
        return await super().on_model_change(data, model, is_created, request)


class ProductAdmin(ModelView, model=Product):
    column_list = [Product.id, Product.title, Product.price, Product.quantity, 
                   Product.status, Product.approval_status, Product.seller_id]
    column_searchable_list = [Product.title, Product.sku]
    column_sortable_list = [Product.id, Product.title, Product.price, Product.created_at]
    form_excluded_columns = [Product.created_at, Product.updated_at]
    
    name = "Product"
    name_plural = "Products"
    icon = "fa-solid fa-box"


class CategoryAdmin(ModelView, model=Category):
    column_list = [Category.id, Category.name, Category.slug, Category.parent_id, Category.is_active]
    column_searchable_list = [Category.name, Category.slug]
    column_sortable_list = [Category.id, Category.name, Category.position]
    form_excluded_columns = [Category.created_at]
    
    name = "Category"
    name_plural = "Categories"
    icon = "fa-solid fa-folder"


class OrderAdmin(ModelView, model=Order):
    column_list = [Order.id, Order.order_number, Order.buyer_id, Order.status, 
                   Order.payment_status, Order.total, Order.created_at]
    column_searchable_list = [Order.order_number]
    column_sortable_list = [Order.id, Order.created_at, Order.total]
    form_excluded_columns = [Order.created_at, Order.updated_at]
    
    name = "Order"
    name_plural = "Orders"
    icon = "fa-solid fa-shopping-cart"


class OrderItemAdmin(ModelView, model=OrderItem):
    column_list = [OrderItem.id, OrderItem.order_id, OrderItem.product_id, 
                   OrderItem.quantity, OrderItem.price, OrderItem.total]
    column_sortable_list = [OrderItem.id, OrderItem.created_at]
    form_excluded_columns = [OrderItem.created_at]
    
    name = "Order Item"
    name_plural = "Order Items"
    icon = "fa-solid fa-list"


class PaymentAdmin(ModelView, model=Payment):
    column_list = [Payment.id, Payment.order_id, Payment.stripe_payment_id, 
                   Payment.amount, Payment.status, Payment.created_at]
    column_searchable_list = [Payment.stripe_payment_id]
    form_excluded_columns = [Payment.created_at]
    
    name = "Payment"
    name_plural = "Payments"
    icon = "fa-solid fa-credit-card"


class AddressAdmin(ModelView, model=Address):
    column_list = [Address.id, Address.user_id, Address.type, Address.city, 
                   Address.country, Address.is_default]
    form_excluded_columns = [Address.created_at]
    
    name = "Address"
    name_plural = "Addresses"
    icon = "fa-solid fa-map-marker"


class ReviewAdmin(ModelView, model=Review):
    column_list = [Review.id, Review.product_id, Review.user_id, Review.rating, 
                   Review.is_verified_purchase, Review.created_at]
    column_sortable_list = [Review.id, Review.rating, Review.created_at]
    form_excluded_columns = [Review.created_at, Review.updated_at]
    
    name = "Review"
    name_plural = "Reviews"
    icon = "fa-solid fa-star"


class ProductImageAdmin(ModelView, model=ProductImage):
    column_list = [ProductImage.id, ProductImage.product_id, ProductImage.image_url, 
                   ProductImage.position]
    column_sortable_list = [ProductImage.id, ProductImage.position]
    form_excluded_columns = [ProductImage.created_at]
    
    name = "Product Image"
    name_plural = "Product Images"
    icon = "fa-solid fa-image"


class CartItemAdmin(ModelView, model=CartItem):
    column_list = [CartItem.id, CartItem.user_id, CartItem.product_id, 
                   CartItem.quantity, CartItem.created_at]
    form_excluded_columns = [CartItem.created_at, CartItem.updated_at]
    
    name = "Cart Item"
    name_plural = "Cart Items"
    icon = "fa-solid fa-shopping-basket"


class WishlistAdmin(ModelView, model=Wishlist):
    column_list = [Wishlist.id, Wishlist.user_id, Wishlist.product_id, Wishlist.created_at]
    form_excluded_columns = [Wishlist.created_at]
    
    name = "Wishlist Item"
    name_plural = "Wishlist"
    icon = "fa-solid fa-heart"


class CouponAdmin(ModelView, model=Coupon):
    column_list = [Coupon.id, Coupon.code, Coupon.type, Coupon.value, 
                   Coupon.is_active, Coupon.expires_at]
    column_searchable_list = [Coupon.code]
    form_excluded_columns = [Coupon.created_at]
    
    name = "Coupon"
    name_plural = "Coupons"
    icon = "fa-solid fa-ticket"


class MessageAdmin(ModelView, model=Message):
    column_list = [Message.id, Message.sender_id, Message.receiver_id, 
                   Message.subject, Message.is_read, Message.created_at]
    form_excluded_columns = [Message.created_at]
    
    name = "Message"
    name_plural = "Messages"
    icon = "fa-solid fa-envelope"


class NotificationAdmin(ModelView, model=Notification):
    column_list = [Notification.id, Notification.user_id, Notification.type, 
                   Notification.title, Notification.is_read, Notification.created_at]
    form_excluded_columns = [Notification.created_at]
    
    name = "Notification"
    name_plural = "Notifications"
    icon = "fa-solid fa-bell"


def register_admin_views(admin):
    """Register all admin views"""
    admin.add_view(UserAdmin)
    admin.add_view(ProductAdmin)
    admin.add_view(CategoryAdmin)
    admin.add_view(ProductImageAdmin)
    admin.add_view(OrderAdmin)
    admin.add_view(OrderItemAdmin)
    admin.add_view(PaymentAdmin)
    admin.add_view(AddressAdmin)
    admin.add_view(ReviewAdmin)
    admin.add_view(CartItemAdmin)
    admin.add_view(WishlistAdmin)
    admin.add_view(CouponAdmin)
    admin.add_view(MessageAdmin)
    admin.add_view(NotificationAdmin)

