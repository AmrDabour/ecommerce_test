from rest_framework import permissions
from .models import UserRole


class IsAdmin(permissions.BasePermission):
    """
    Permission check: User must be an admin.
    """
    message = "Only administrators can perform this action."
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.ADMIN
        )


class IsVendor(permissions.BasePermission):
    """
    Permission check: User must be a vendor.
    """
    message = "Only vendors can perform this action."
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.VENDOR
        )


class IsCustomer(permissions.BasePermission):
    """
    Permission check: User must be a customer.
    """
    message = "Only customers can perform this action."
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.CUSTOMER
        )


class IsApprovedVendor(permissions.BasePermission):
    """
    Permission check: User must be an approved vendor.
    """
    message = "Your vendor account is not approved yet."
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if request.user.role != UserRole.VENDOR:
            return False
        
        if not hasattr(request.user, 'vendor_profile'):
            return False
        
        return request.user.vendor_profile.is_approved


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission check: User must own the object or be an admin.
    Object must have 'user' attribute.
    """
    message = "You do not have permission to access this resource."
    
    def has_object_permission(self, request, view, obj):
        # Admin has full access
        if request.user.role == UserRole.ADMIN:
            return True
        
        # Owner has access
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class IsVendorOwnerOrAdmin(permissions.BasePermission):
    """
    Permission check: User must be the vendor who owns the object, or an admin.
    Object must have 'vendor' attribute.
    """
    message = "You do not have permission to access this resource."
    
    def has_object_permission(self, request, view, obj):
        # Admin has full access
        if request.user.role == UserRole.ADMIN:
            return True
        
        # Vendor owner has access
        if hasattr(obj, 'vendor'):
            return obj.vendor == request.user
        
        return False


class IsCustomerOwnerOrAdmin(permissions.BasePermission):
    """
    Permission check: User must be the customer who owns the object, or an admin.
    Object must have 'customer' attribute.
    """
    message = "You do not have permission to access this resource."
    
    def has_object_permission(self, request, view, obj):
        # Admin has full access
        if request.user.role == UserRole.ADMIN:
            return True
        
        # Customer owner has access
        if hasattr(obj, 'customer'):
            return obj.customer == request.user
        
        return False


class ReadOnly(permissions.BasePermission):
    """
    Permission check: Allow read-only access (GET, HEAD, OPTIONS).
    """
    
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission check: Admin can edit, everyone can read.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.ADMIN
        )


class CanApplyForVendorAccount(permissions.BasePermission):
    """
    Permission check: User can apply for vendor account.
    Must be a customer without existing vendor profile.
    """
    message = "You cannot apply for a vendor account."
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Must be a customer
        if request.user.role != UserRole.CUSTOMER:
            self.message = "Only customers can apply for vendor accounts."
            return False
        
        # Must not already have vendor profile
        if hasattr(request.user, 'vendor_profile'):
            self.message = "You already have a vendor account."
            return False
        
        return True


class IsEmailVerified(permissions.BasePermission):
    """
    Permission check: User's email must be verified.
    """
    message = "Please verify your email address first."
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.email_verified
        )
