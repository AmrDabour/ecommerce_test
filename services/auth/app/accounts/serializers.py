from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer
from .models import VendorProfile, CustomerProfile, Address, UserRole

User = get_user_model()


class UserCreateSerializer(DjoserUserCreateSerializer):
    """
    Custom user registration serializer.
    Extends Djoser's UserCreateSerializer to include role-based defaults.
    """
    
    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'password', 'first_name', 'last_name', 'phone_number')
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 8},
        }
    
    def validate_email(self, value):
        """Ensure email is unique (case-insensitive)"""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()
    
    def create(self, validated_data):
        """Create user with CUSTOMER role by default"""
        validated_data['role'] = UserRole.CUSTOMER
        validated_data['is_active'] = True  # Active by default, email verification optional
        user = super().create(validated_data)
        
        # Auto-create CustomerProfile
        CustomerProfile.objects.create(user=user)
        
        return user


class UserSerializer(DjoserUserSerializer):
    """
    Current user serializer with role information.
    """
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    is_admin = serializers.BooleanField(read_only=True)
    is_vendor = serializers.BooleanField(read_only=True)
    is_customer = serializers.BooleanField(read_only=True)
    
    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'phone_number',
            'role', 'role_display', 'is_admin', 'is_vendor', 'is_customer',
            'is_active', 'email_verified', 'created_at'
        )
        read_only_fields = ('id', 'email', 'role', 'is_active', 'email_verified', 'created_at')


class VendorProfileSerializer(serializers.ModelSerializer):
    """
    VendorProfile serializer for vendor dashboard.
    SECURITY: status, commission_rate, stats are read-only.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = VendorProfile
        fields = (
            'user', 'user_email', 'business_name', 'business_description',
            'business_registration_number', 'business_email', 'business_phone',
            'business_address', 'business_city', 'business_state',
            'business_country', 'business_postal_code',
            'logo', 'banner', 'status', 'status_display',
            'commission_rate', 'total_sales', 'total_products',
            'is_featured', 'created_at', 'updated_at'
        )
        read_only_fields = (
            # Identity & ownership
            'user', 'user_email',
            # Approval workflow (ADMIN ONLY)
            'status', 'status_display', 'approved_by', 'approved_at', 'rejection_reason',
            # Financial & stats (SYSTEM ONLY)
            'commission_rate', 'total_sales', 'total_products',
            # Admin privileges
            'is_featured',
            # Timestamps
            'created_at', 'updated_at'
        )


class VendorOnboardingSerializer(serializers.Serializer):
    """
    Vendor onboarding request (Customer → Vendor).
    Separate from VendorProfile for security.
    """
    business_name = serializers.CharField(max_length=255)
    business_description = serializers.CharField()
    business_registration_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    business_email = serializers.EmailField()
    business_phone = serializers.CharField(max_length=17, required=False, allow_blank=True)
    business_address = serializers.CharField(required=False, allow_blank=True)
    business_city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    business_state = serializers.CharField(max_length=100, required=False, allow_blank=True)
    business_country = serializers.CharField(max_length=100)
    business_postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    def validate_business_name(self, value):
        """Ensure business name is unique"""
        if VendorProfile.objects.filter(business_name__iexact=value).exists():
            raise serializers.ValidationError("A vendor with this business name already exists.")
        return value
    
    def validate(self, attrs):
        """Ensure user is a customer and doesn't already have vendor profile"""
        user = self.context['request'].user
        
        if user.role != UserRole.CUSTOMER:
            raise serializers.ValidationError("Only customers can apply for vendor account.")
        
        if hasattr(user, 'vendor_profile'):
            raise serializers.ValidationError("You already have a vendor account.")
        
        return attrs
    
    def create(self, validated_data):
        """Create vendor profile with PENDING status"""
        user = self.context['request'].user
        
        vendor_profile = VendorProfile.objects.create(
            user=user,
            status=VendorProfile.VendorStatus.PENDING,
            **validated_data
        )
        
        # Update user role to VENDOR
        user.role = UserRole.VENDOR
        user.is_active = False  # Deactivate until admin approval
        user.save(update_fields=['role', 'is_active'])
        
        return vendor_profile


class VendorApprovalSerializer(serializers.Serializer):
    """
    Admin approval/rejection of vendor accounts.
    """
    action = serializers.ChoiceField(choices=['approve', 'reject', 'suspend'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    commission_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        min_value=0,
        max_value=100
    )
    
    def validate(self, attrs):
        """Ensure rejection reason provided when rejecting"""
        if attrs['action'] == 'reject' and not attrs.get('rejection_reason'):
            raise serializers.ValidationError({
                'rejection_reason': 'Rejection reason is required when rejecting vendor.'
            })
        return attrs


class CustomerProfileSerializer(serializers.ModelSerializer):
    """
    CustomerProfile serializer.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = CustomerProfile
        fields = (
            'user', 'user_email', 'full_name', 'date_of_birth', 'avatar',
            'loyalty_points', 'newsletter_subscribed',
            'total_orders', 'total_spent',
            'preferred_currency', 'preferred_language',
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'user', 'loyalty_points', 'total_orders', 'total_spent',
            'created_at', 'updated_at'
        )


class AddressSerializer(serializers.ModelSerializer):
    """
    Address serializer for shipping/billing addresses.
    """
    address_type_display = serializers.CharField(source='get_address_type_display', read_only=True)
    
    class Meta:
        model = Address
        fields = (
            'id', 'user', 'address_type', 'address_type_display',
            'full_name', 'phone_number',
            'address_line1', 'address_line2',
            'city', 'state_province', 'postal_code', 'country',
            'is_default', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')
    
    def validate(self, attrs):
        """Ensure only one default address per type per user"""
        user = self.context['request'].user
        
        if attrs.get('is_default'):
            # Unset other default addresses of same type
            Address.objects.filter(
                user=user,
                address_type=attrs['address_type'],
                is_default=True
            ).update(is_default=False)
        
        return attrs
    
    def create(self, validated_data):
        """Auto-set user from request"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AddressCreateSerializer(AddressSerializer):
    """Separate serializer for address creation (hides user field from input)"""
    
    class Meta(AddressSerializer.Meta):
        fields = tuple(f for f in AddressSerializer.Meta.fields if f != 'user')


class PasswordChangeSerializer(serializers.Serializer):
    """
    Change password for authenticated users.
    Uses Djoser but adds extra validation.
    """
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    
    def validate_current_password(self, value):
        """Check current password is correct"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value
    
    def validate_new_password(self, value):
        """Validate new password"""
        validate_password(value, user=self.context['request'].user)
        return value
    
    def validate(self, attrs):
        """Ensure new password is different from current"""
        if attrs['current_password'] == attrs['new_password']:
            raise serializers.ValidationError({
                'new_password': 'New password must be different from current password.'
            })
        return attrs


class PublicVendorProfileSerializer(serializers.ModelSerializer):
    """
    Public-facing vendor profile (for customers browsing vendors).
    Hides sensitive business information.
    """
    total_products_count = serializers.IntegerField(source='total_products', read_only=True)
    
    class Meta:
        model = VendorProfile
        fields = (
            'business_name', 'business_description',
            'logo', 'banner', 'is_featured',
            'total_products_count', 'created_at'
        )
        read_only_fields = fields
