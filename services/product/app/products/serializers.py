from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Product, ProductStatus, Category, Brand,
    ProductImage, ProductVariant, ProductAttribute,
    ProductReview, Wishlist
)

# Note: In microservices, vendor information should be fetched via API call to auth-service
# For now, we'll use vendor_id directly or fetch vendor name via API

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    """Category serializer with parent hierarchy"""
    full_path = serializers.CharField(source='get_full_path', read_only=True)
    children_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = (
            'id', 'name', 'slug', 'description', 'parent',
            'image', 'is_active', 'display_order',
            'full_path', 'children_count', 'created_at'
        )
        read_only_fields = ('id', 'slug', 'created_at')
    
    def get_children_count(self, obj):
        return obj.children.count() if hasattr(obj, 'children') else 0


class BrandSerializer(serializers.ModelSerializer):
    """Brand serializer"""
    
    class Meta:
        model = Brand
        fields = ('id', 'name', 'slug', 'description', 'logo', 'website', 'is_active', 'created_at')
        read_only_fields = ('id', 'slug', 'created_at')


class ProductImageSerializer(serializers.ModelSerializer):
    """Product image serializer"""
    
    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'alt_text', 'is_primary', 'display_order', 'created_at')
        read_only_fields = ('id', 'created_at')


class ProductVariantSerializer(serializers.ModelSerializer):
    """Product variant serializer"""
    effective_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = ProductVariant
        fields = (
            'id', 'name', 'sku', 'price', 'effective_price',
            'stock_quantity', 'weight', 'image',
            'is_active', 'created_at'
        )
        read_only_fields = ('id', 'created_at', 'effective_price')


class ProductAttributeSerializer(serializers.ModelSerializer):
    """Product attribute serializer"""
    
    class Meta:
        model = ProductAttribute
        fields = ('id', 'name', 'value', 'display_order')
        read_only_fields = ('id',)


class ProductListSerializer(serializers.ModelSerializer):
    """
    Optimized product serializer for list views.
    Only essential fields for performance.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True, allow_null=True)
    vendor_id = serializers.IntegerField(source='vendor_id', read_only=True)
    # Note: vendor_name should be fetched via API call to auth-service if needed
    primary_image = serializers.SerializerMethodField()
    discount_percentage = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'sku',
            'category_name', 'brand_name', 'vendor_id',
            'price', 'compare_at_price', 'discount_percentage',
            'stock_quantity', 'is_in_stock',
            'primary_image', 'is_featured',
            'sales_count', 'created_at'
        )
    
    def get_primary_image(self, obj):
        """Get primary product image URL"""
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(primary.image.url)
            return primary.image.url
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Detailed product serializer for single product view.
    Includes all related data.
    """
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    vendor_id = serializers.IntegerField(source='vendor_id', read_only=True)
    # Note: vendor_profile should be fetched via API call to auth-service if needed
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    attributes = ProductAttributeSerializer(many=True, read_only=True)
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_approved = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'sku', 'description', 'short_description',
            'category', 'brand', 'vendor_id',
            'price', 'compare_at_price', 'discount_percentage',
            'stock_quantity', 'low_stock_threshold',
            'track_inventory', 'allow_backorders',
            'is_in_stock', 'is_low_stock',
            'weight', 'length', 'width', 'height',
            'status', 'status_display', 'is_approved',
            'rejection_reason', 'is_featured', 'is_active',
            'view_count', 'sales_count',
            'images', 'variants', 'attributes',
            'meta_title', 'meta_description', 'meta_keywords',
            'created_at', 'updated_at', 'published_at'
        )


class ProductCreateSerializer(serializers.ModelSerializer):
    """
    Product creation serializer (vendor use).
    Separate from detail to control writable fields.
    """
    
    class Meta:
        model = Product
        fields = (
            'name', 'sku', 'description', 'short_description',
            'category', 'brand',
            'price', 'compare_at_price', 'cost_price',
            'stock_quantity', 'low_stock_threshold',
            'track_inventory', 'allow_backorders',
            'weight', 'length', 'width', 'height',
            'meta_title', 'meta_description', 'meta_keywords',
            'is_active'
        )
    
    def validate_sku(self, value):
        """Ensure SKU is unique"""
        if Product.objects.filter(sku=value).exists():
            raise serializers.ValidationError("Product with this SKU already exists.")
        return value
    
    def validate(self, attrs):
        """Business logic validation"""
        if attrs.get('compare_at_price') and attrs['compare_at_price'] <= attrs['price']:
            raise serializers.ValidationError({
                'compare_at_price': 'Compare at price must be greater than regular price.'
            })
        return attrs
    
    def create(self, validated_data):
        """Create product with vendor and default status"""
        validated_data['vendor'] = self.context['request'].user
        validated_data['status'] = ProductStatus.DRAFT
        return super().create(validated_data)


class ProductUpdateSerializer(serializers.ModelSerializer):
    """
    Product update serializer.
    Vendors can update most fields, but not status.
    """
    
    class Meta:
        model = Product
        fields = (
            'name', 'description', 'short_description',
            'category', 'brand',
            'price', 'compare_at_price', 'cost_price',
            'stock_quantity', 'low_stock_threshold',
            'track_inventory', 'allow_backorders',
            'weight', 'length', 'width', 'height',
            'meta_title', 'meta_description', 'meta_keywords',
            'is_active'
        )
    
    def validate(self, attrs):
        """Prevent editing approved products without un-approval"""
        instance = self.instance
        if instance.status == ProductStatus.APPROVED:
            # Admin can edit approved products
            if not self.context['request'].user.is_admin:
                raise serializers.ValidationError(
                    "Cannot edit approved products. Please contact admin or create a new version."
                )
        return attrs


class ProductApprovalSerializer(serializers.Serializer):
    """Admin product approval/rejection"""
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        if attrs['action'] == 'reject' and not attrs.get('rejection_reason'):
            raise serializers.ValidationError({
                'rejection_reason': 'Rejection reason is required when rejecting product.'
            })
        return attrs


class ProductReviewSerializer(serializers.ModelSerializer):
    """Product review serializer"""
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    customer_avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductReview
        fields = (
            'id', 'product', 'customer', 'customer_name', 'customer_avatar',
            'rating', 'title', 'comment',
            'is_verified_purchase', 'is_approved',
            'helpful_count', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'customer', 'is_verified_purchase', 'is_approved',
            'helpful_count', 'created_at', 'updated_at'
        )
    
    def get_customer_avatar(self, obj):
        """Get customer avatar URL if exists"""
        if hasattr(obj.customer, 'customer_profile') and obj.customer.customer_profile.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.customer.customer_profile.avatar.url)
        return None
    
    def validate_rating(self, value):
        """Ensure rating is 1-5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
    
    def create(self, validated_data):
        """Auto-set customer from request"""
        validated_data['customer'] = self.context['request'].user
        validated_data['is_approved'] = False  # Requires admin moderation
        
        # TODO: Check if verified purchase
        # validated_data['is_verified_purchase'] = check_if_purchased(user, product)
        
        return super().create(validated_data)


class WishlistSerializer(serializers.ModelSerializer):
    """Wishlist serializer"""
    product_detail = ProductListSerializer(source='product', read_only=True)
    
    class Meta:
        model = Wishlist
        fields = ('id', 'product', 'product_detail', 'created_at')
        read_only_fields = ('id', 'created_at')
    
    def create(self, validated_data):
        """Auto-set customer from request"""
        validated_data['customer'] = self.context['request'].user
        return super().create(validated_data)
