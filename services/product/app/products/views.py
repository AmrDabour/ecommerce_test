from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import (
    Product, ProductStatus, Category, Brand,
    ProductImage, ProductVariant, ProductAttribute,
    ProductReview, Wishlist
)
from .serializers import (
    ProductListSerializer, ProductDetailSerializer,
    ProductCreateSerializer, ProductUpdateSerializer,
    ProductApprovalSerializer,
    CategorySerializer, BrandSerializer,
    ProductImageSerializer, ProductVariantSerializer,
    ProductAttributeSerializer,
    ProductReviewSerializer, WishlistSerializer
)


class ProductViewSet(viewsets.ModelViewSet):
    """
    Product CRUD and management
    - List: All approved products (public)
    - Retrieve: Product details (public)
    - Create: Vendors only
    - Update/Delete: Owner vendor or admin only
    """
    queryset = Product.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'brand', 'status', 'is_featured', 'is_active']
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['price', 'created_at', 'sales_count', 'view_count']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        elif self.action in ['create']:
            return ProductCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ProductUpdateSerializer
        return ProductDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Public: only approved, active products
        if self.action in ['list', 'retrieve']:
            queryset = queryset.filter(
                status=ProductStatus.APPROVED,
                is_active=True
            )

        # Vendor: see own products
        elif self.request.user.is_authenticated and hasattr(self.request.user, 'vendor_profile'):
            queryset = queryset.filter(vendor_id=self.request.user.id)

        return queryset.select_related('category', 'brand').prefetch_related('images', 'variants')

    def create(self, request, *args, **kwargs):
        """Only vendors can create products"""
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not hasattr(request.user, 'vendor_profile'):
            return Response(
                {'detail': 'Only vendors can create products'},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        """Admin approves or rejects product"""
        product = self.get_object()
        serializer = ProductApprovalSerializer(data=request.data)

        if serializer.is_valid():
            if serializer.validated_data['action'] == 'approve':
                product.status = ProductStatus.APPROVED
                product.rejection_reason = ''
            else:
                product.status = ProductStatus.REJECTED
                product.rejection_reason = serializer.validated_data.get('rejection_reason', '')

            product.approved_by_id = request.user.id
            product.save()

            return Response({'status': 'Product updated successfully'})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryViewSet(viewsets.ModelViewSet):
    """Category CRUD"""
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = super().get_queryset()
        # Only root categories for top-level listing
        if self.action == 'list' and self.request.query_params.get('root'):
            queryset = queryset.filter(parent__isnull=True)
        return queryset


class BrandViewSet(viewsets.ModelViewSet):
    """Brand CRUD"""
    queryset = Brand.objects.filter(is_active=True)
    serializer_class = BrandSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'


class ProductReviewViewSet(viewsets.ModelViewSet):
    """Product reviews"""
    queryset = ProductReview.objects.filter(is_approved=True)
    serializer_class = ProductReviewSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['product', 'rating']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """Only customers can create reviews"""
        if not hasattr(request.user, 'customer_profile'):
            return Response(
                {'detail': 'Only customers can create reviews'},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().create(request, *args, **kwargs)


class WishlistViewSet(viewsets.ModelViewSet):
    """Customer wishlist"""
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only show current user's wishlist
        return super().get_queryset().filter(customer_id=self.request.user.id)

    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """Toggle product in wishlist"""
        product_id = request.data.get('product_id')
        if not product_id:
            return Response(
                {'detail': 'product_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        wishlist_item = Wishlist.objects.filter(
            customer_id=request.user.id,
            product_id=product_id
        ).first()

        if wishlist_item:
            wishlist_item.delete()
            return Response({'status': 'removed', 'in_wishlist': False})
        else:
            Wishlist.objects.create(
                customer_id=request.user.id,
                product_id=product_id
            )
            return Response({'status': 'added', 'in_wishlist': True})
