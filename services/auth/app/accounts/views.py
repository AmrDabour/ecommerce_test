"""
ViewSets for accounts app.
Views are THIN - they only orchestrate.
All business logic is in services.py.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django_filters.rest_framework import DjangoFilterBackend

from .models import VendorProfile, CustomerProfile, Address, UserRole
from .serializers import (
    VendorProfileSerializer,
    VendorOnboardingSerializer,
    VendorApprovalSerializer,
    CustomerProfileSerializer,
    AddressSerializer,
    AddressCreateSerializer,
    PublicVendorProfileSerializer,
)
from .permissions import (
    IsAdmin,
    IsVendor,
    IsCustomer,
    IsOwnerOrAdmin,
    CanApplyForVendorAccount,
)
from .services import (
    VendorOnboardingService,
    AddressService,
    VendorSelectors,
)

User = get_user_model()


class VendorProfileViewSet(viewsets.ModelViewSet):
    """
    Vendor profile management.
    Thin view - delegates to services.
    """
    queryset = VendorProfile.objects.select_related('user', 'approved_by').all()
    serializer_class = VendorProfileSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'is_featured', 'business_country']
    search_fields = ['business_name', 'business_description', 'business_email']
    ordering_fields = ['created_at', 'total_sales', 'total_products']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """Dynamic permissions based on action"""
        if self.action in ['list', 'retrieve', 'public_vendors']:
            return [IsAuthenticated()]
        elif self.action == 'approve_vendor':
            return [IsAdmin()]
        elif self.action in ['update', 'partial_update']:
            return [IsVendor(), IsOwnerOrAdmin()]
        elif self.action == 'destroy':
            return [IsAdmin()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """
        Role-based queryset filtering.
        Delegates to selectors for complex queries.
        """
        user = self.request.user
        
        if user.role == UserRole.ADMIN:
            return self.queryset
        elif user.role == UserRole.VENDOR:
            return self.queryset.filter(user=user)
        else:
            # Customers see only approved vendors (use selector)
            return VendorSelectors.get_approved_vendors()
    
    def get_serializer_class(self):
        """Use public serializer for public endpoints"""
        if self.action == 'public_vendors':
            return PublicVendorProfileSerializer
        return self.serializer_class
    
    @action(detail=False, methods=['post'], permission_classes=[CanApplyForVendorAccount])
    def apply(self, request):
        """
        Customer applies for vendor account.
        Orchestrates VendorOnboardingService.
        """
        serializer = VendorOnboardingSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        try:
            # Delegate to service
            vendor_profile = VendorOnboardingService.apply_for_vendor_account(
                user=request.user,
                business_data=serializer.validated_data
            )
        except DjangoValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(
            {
                'message': 'Vendor application submitted successfully. '
                          'Your account will be reviewed by our team.',
                'vendor_profile': VendorProfileSerializer(vendor_profile).data
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def approve_vendor(self, request, pk=None):
        """
        Admin approves/rejects/suspends vendor.
        Orchestrates VendorOnboardingService.
        """
        vendor_profile = self.get_object()
        serializer = VendorApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action_type = serializer.validated_data['action']
        
        try:
            if action_type == 'approve':
                vendor_profile = VendorOnboardingService.approve_vendor(
                    vendor_profile=vendor_profile,
                    admin_user=request.user,
                    commission_rate=serializer.validated_data.get('commission_rate')
                )
                message = f'Vendor "{vendor_profile.business_name}" has been approved.'
            
            elif action_type == 'reject':
                vendor_profile = VendorOnboardingService.reject_vendor(
                    vendor_profile=vendor_profile,
                    admin_user=request.user,
                    rejection_reason=serializer.validated_data.get('rejection_reason')
                )
                message = f'Vendor "{vendor_profile.business_name}" has been rejected.'
            
            elif action_type == 'suspend':
                vendor_profile = VendorOnboardingService.suspend_vendor(
                    vendor_profile=vendor_profile,
                    admin_user=request.user,
                    reason=serializer.validated_data.get('rejection_reason')
                )
                message = f'Vendor "{vendor_profile.business_name}" has been suspended.'
            
        except DjangoValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(
            {
                'message': message,
                'vendor_profile': VendorProfileSerializer(vendor_profile).data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def public_vendors(self, request):
        """
        Public list of approved vendors (storefront).
        Uses selector for optimized query.
        """
        vendors = VendorSelectors.get_approved_vendors()
        
        page = self.paginate_queryset(vendors)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(vendors, many=True)
        return Response(serializer.data)


class CustomerProfileViewSet(viewsets.ModelViewSet):
    """
    Customer profile management.
    Thin view - minimal logic.
    """
    queryset = CustomerProfile.objects.select_related('user').all()
    serializer_class = CustomerProfileSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['total_orders', 'total_spent', 'loyalty_points']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Role-based filtering"""
        user = self.request.user
        
        if user.role == UserRole.ADMIN:
            return self.queryset
        elif user.role == UserRole.CUSTOMER:
            return self.queryset.filter(user=user)
        else:
            return self.queryset.none()
    
    def get_permissions(self):
        """Prevent manual creation/deletion"""
        if self.action in ['create', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated(), IsOwnerOrAdmin()]
    
    @action(detail=False, methods=['get'], permission_classes=[IsCustomer])
    def me(self, request):
        """Get current customer's profile"""
        try:
            profile = CustomerProfile.objects.select_related('user').get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except CustomerProfile.DoesNotExist:
            return Response(
                {'error': 'Customer profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )


class AddressViewSet(viewsets.ModelViewSet):
    """
    Address management.
    Delegates address logic to AddressService.
    """
    queryset = Address.objects.select_related('user').all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['address_type', 'is_default', 'country']
    ordering = ['-is_default', '-created_at']
    
    def get_queryset(self):
        """Users see only own addresses, admins see all"""
        user = self.request.user
        
        if user.role == UserRole.ADMIN:
            return self.queryset
        else:
            return self.queryset.filter(user=user)
    
    def get_serializer_class(self):
        """Use create serializer for POST"""
        if self.action == 'create':
            return AddressCreateSerializer
        return self.serializer_class
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def set_default(self, request, pk=None):
        """
        Set address as default.
        Delegates to AddressService.
        """
        address = self.get_object()
        
        try:
            address = AddressService.set_default_address(
                address=address,
                user=request.user
            )
        except DjangoValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(address)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def default_shipping(self, request):
        """
        Get default shipping address.
        Uses AddressService selector.
        """
        address = AddressService.get_default_address(
            user=request.user,
            address_type='SHIPPING'
        )
        
        if not address:
            return Response(
                {'error': 'No default shipping address found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(address)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def default_billing(self, request):
        """
        Get default billing address.
        Uses AddressService selector.
        """
        address = AddressService.get_default_address(
            user=request.user,
            address_type='BILLING'
        )
        
        if not address:
            return Response(
                {'error': 'No default billing address found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(address)
        return Response(serializer.data)
