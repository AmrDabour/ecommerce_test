"""
Business logic layer for accounts app.
All business rules and workflows are centralized here.
Views should ONLY orchestrate, not contain logic.
"""
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import User, VendorProfile, CustomerProfile, Address, UserRole


class VendorOnboardingService:
    """
    Handles vendor onboarding workflow.
    Customer → Vendor application with admin approval.
    """
    
    @staticmethod
    def apply_for_vendor_account(user, business_data):
        """
        Customer applies for vendor account.
        
        Args:
            user: User instance (must be CUSTOMER)
            business_data: dict with business information
        
        Returns:
            VendorProfile instance
        
        Raises:
            ValidationError: If user is not eligible
        """
        # Validation: User must be customer
        if user.role != UserRole.CUSTOMER:
            raise ValidationError("Only customers can apply for vendor accounts.")
        
        # Validation: No existing vendor profile
        if hasattr(user, 'vendor_profile'):
            raise ValidationError("You already have a vendor account.")
        
        # Validation: Business name must be unique
        if VendorProfile.objects.filter(
            business_name__iexact=business_data.get('business_name')
        ).exists():
            raise ValidationError("A vendor with this business name already exists.")
        
        # Create vendor profile with PENDING status
        with transaction.atomic():
            vendor_profile = VendorProfile.objects.create(
                user=user,
                status=VendorProfile.VendorStatus.PENDING,
                **business_data
            )
            
            # Update user role to VENDOR (inactive until approval)
            user.role = UserRole.VENDOR
            user.is_active = False  # Requires admin approval
            user.save(update_fields=['role', 'is_active'])
            
            # TODO: Send notification to admins
            # from notifications.tasks import notify_admins_vendor_application
            # notify_admins_vendor_application.delay(vendor_profile.pk)
        
        return vendor_profile
    
    @staticmethod
    def approve_vendor(vendor_profile, admin_user, commission_rate=None):
        """
        Admin approves vendor account.
        
        Args:
            vendor_profile: VendorProfile instance
            admin_user: Admin User instance
            commission_rate: Optional commission rate override
        
        Returns:
            Updated VendorProfile instance
        
        Raises:
            ValidationError: If vendor cannot be approved
        """
        # Validation: Only pending vendors can be approved
        if vendor_profile.status != VendorProfile.VendorStatus.PENDING:
            raise ValidationError(
                f"Cannot approve vendor with status: {vendor_profile.get_status_display()}"
            )
        
        with transaction.atomic():
            # Update vendor profile
            vendor_profile.status = VendorProfile.VendorStatus.APPROVED
            vendor_profile.approved_by = admin_user
            vendor_profile.approved_at = timezone.now()
            vendor_profile.rejection_reason = ''
            
            if commission_rate is not None:
                vendor_profile.commission_rate = commission_rate
            
            vendor_profile.save()
            
            # Activate vendor user
            vendor_profile.user.is_active = True
            vendor_profile.user.save(update_fields=['is_active'])
            
            # TODO: Send approval email
            # from notifications.tasks import send_vendor_approval_email
            # send_vendor_approval_email.delay(vendor_profile.pk)
        
        return vendor_profile
    
    @staticmethod
    def reject_vendor(vendor_profile, admin_user, rejection_reason):
        """
        Admin rejects vendor account.
        
        Args:
            vendor_profile: VendorProfile instance
            admin_user: Admin User instance
            rejection_reason: str, reason for rejection
        
        Returns:
            Updated VendorProfile instance
        """
        if not rejection_reason:
            raise ValidationError("Rejection reason is required.")
        
        with transaction.atomic():
            vendor_profile.status = VendorProfile.VendorStatus.REJECTED
            vendor_profile.rejection_reason = rejection_reason
            vendor_profile.save()
            
            # Keep user inactive
            vendor_profile.user.is_active = False
            vendor_profile.user.save(update_fields=['is_active'])
            
            # TODO: Send rejection email
            # from notifications.tasks import send_vendor_rejection_email
            # send_vendor_rejection_email.delay(vendor_profile.pk, rejection_reason)
        
        return vendor_profile
    
    @staticmethod
    def suspend_vendor(vendor_profile, admin_user, reason=None):
        """
        Admin suspends vendor account.
        
        Args:
            vendor_profile: VendorProfile instance
            admin_user: Admin User instance
            reason: Optional suspension reason
        """
        with transaction.atomic():
            vendor_profile.status = VendorProfile.VendorStatus.SUSPENDED
            if reason:
                vendor_profile.rejection_reason = reason  # Reuse field for suspension reason
            vendor_profile.save()
            
            # Deactivate user
            vendor_profile.user.is_active = False
            vendor_profile.user.save(update_fields=['is_active'])
            
            # TODO: Send suspension email
            # from notifications.tasks import send_vendor_suspension_email
            # send_vendor_suspension_email.delay(vendor_profile.pk, reason)
        
        return vendor_profile


class AddressService:
    """
    Handles address management logic.
    """
    
    @staticmethod
    def set_default_address(address, user):
        """
        Set an address as default for its type.
        Unsets other defaults of same type.
        
        Args:
            address: Address instance
            user: User instance (for ownership validation)
        
        Raises:
            ValidationError: If user doesn't own address
        """
        # Security: Ensure user owns this address
        if address.user != user:
            raise ValidationError("You do not have permission to modify this address.")
        
        with transaction.atomic():
            # Unset other defaults of same type
            Address.objects.filter(
                user=user,
                address_type=address.address_type,
                is_default=True
            ).update(is_default=False)
            
            # Set this as default
            address.is_default = True
            address.save(update_fields=['is_default'])
        
        return address
    
    @staticmethod
    def get_default_address(user, address_type):
        """
        Get user's default address for a specific type.
        
        Args:
            user: User instance
            address_type: 'SHIPPING' or 'BILLING'
        
        Returns:
            Address instance or None
        """
        # Map to address type choices
        type_filter = {
            'SHIPPING': [Address.AddressType.SHIPPING, Address.AddressType.BOTH],
            'BILLING': [Address.AddressType.BILLING, Address.AddressType.BOTH],
        }
        
        return Address.objects.filter(
            user=user,
            address_type__in=type_filter.get(address_type, []),
            is_default=True
        ).first()


class CustomerProfileService:
    """
    Handles customer profile logic.
    """
    
    @staticmethod
    def update_loyalty_points(customer_profile, points, operation='add'):
        """
        Update customer loyalty points.
        
        Args:
            customer_profile: CustomerProfile instance
            points: int, number of points
            operation: 'add' or 'subtract'
        """
        if operation == 'add':
            customer_profile.loyalty_points += points
        elif operation == 'subtract':
            customer_profile.loyalty_points = max(0, customer_profile.loyalty_points - points)
        
        customer_profile.save(update_fields=['loyalty_points'])
        return customer_profile
    
    @staticmethod
    def update_order_stats(customer_profile, order_total):
        """
        Update customer order statistics after purchase.
        
        Args:
            customer_profile: CustomerProfile instance
            order_total: Decimal, order total amount
        """
        customer_profile.total_orders += 1
        customer_profile.total_spent += order_total
        customer_profile.save(update_fields=['total_orders', 'total_spent'])
        return customer_profile


class VendorStatsService:
    """
    Handles vendor statistics updates.
    """
    
    @staticmethod
    def update_vendor_sales(vendor_profile, sale_amount):
        """
        Update vendor sales statistics.
        Called after order delivery/completion.
        
        Args:
            vendor_profile: VendorProfile instance
            sale_amount: Decimal, vendor's net sale amount
        """
        vendor_profile.total_sales += sale_amount
        vendor_profile.save(update_fields=['total_sales'])
        return vendor_profile
    
    @staticmethod
    def update_product_count(vendor_profile):
        """
        Recalculate vendor's total approved products.
        Called when product approval status changes.
        
        NOTE: In microservices architecture, this should call product-service API
        to get the count. For now, this method is kept for compatibility but
        should be updated to make HTTP call to product-service.
        
        Args:
            vendor_profile: VendorProfile instance
        """
        # TODO: In microservices, call product-service API to get product count
        # import requests
        # response = requests.get(f'{PRODUCT_SERVICE_URL}/api/v1/products/count/?vendor_id={vendor_profile.user.id}')
        # approved_count = response.json().get('count', 0)
        
        # For now, keep the field but don't update it automatically
        # This should be updated via API call from product-service when products are approved/rejected
        return vendor_profile


# Selector functions (read-only queries)
class VendorSelectors:
    """
    Query methods for vendors (read-only).
    Separates queries from business logic.
    """
    
    @staticmethod
    def get_approved_vendors(featured_only=False):
        """Get all approved vendors, optionally only featured ones."""
        queryset = VendorProfile.objects.select_related('user').filter(
            status=VendorProfile.VendorStatus.APPROVED
        )
        
        if featured_only:
            queryset = queryset.filter(is_featured=True)
        
        return queryset.order_by('-is_featured', '-total_sales')
    
    @staticmethod
    def get_pending_vendor_applications():
        """Get all pending vendor applications (for admin review)."""
        return VendorProfile.objects.select_related('user').filter(
            status=VendorProfile.VendorStatus.PENDING
        ).order_by('created_at')


class CustomerSelectors:
    """
    Query methods for customers (read-only).
    """
    
    @staticmethod
    def get_top_customers_by_spending(limit=10):
        """Get top customers by total spending."""
        return CustomerProfile.objects.select_related('user').order_by(
            '-total_spent'
        )[:limit]
    
    @staticmethod
    def get_customers_with_loyalty_points(min_points=100):
        """Get customers with loyalty points >= min_points."""
        return CustomerProfile.objects.select_related('user').filter(
            loyalty_points__gte=min_points
        ).order_by('-loyalty_points')
