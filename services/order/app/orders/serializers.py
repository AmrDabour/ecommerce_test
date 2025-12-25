from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory, Cart, CartItem, Refund


class OrderItemSerializer(serializers.ModelSerializer):
    """Order item serializer"""

    class Meta:
        model = OrderItem
        fields = (
            'id', 'order', 'product_id', 'variant_id', 'vendor_id',
            'product_name', 'product_sku', 'quantity', 'price',
            'subtotal', 'status', 'created_at'
        )
        read_only_fields = ('id', 'created_at', 'subtotal')


class OrderListSerializer(serializers.ModelSerializer):
    """Order list serializer - minimal fields"""
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            'id', 'order_number', 'customer_id', 'status',
            'subtotal', 'tax_amount', 'shipping_cost', 'discount_amount',
            'total', 'items_count', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'order_number', 'created_at', 'updated_at')

    def get_items_count(self, obj):
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    """Order detail serializer - includes items"""
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            'id', 'order_number', 'customer_id',
            'shipping_address_id', 'billing_address_id',
            'status', 'subtotal', 'tax_amount', 'shipping_cost',
            'discount_amount', 'total', 'payment_method',
            'payment_status', 'notes', 'items',
            'created_at', 'updated_at', 'completed_at', 'cancelled_at'
        )
        read_only_fields = ('id', 'order_number', 'created_at', 'updated_at')


class CartItemSerializer(serializers.ModelSerializer):
    """Cart item serializer"""

    class Meta:
        model = CartItem
        fields = (
            'id', 'cart', 'product_id', 'variant_id',
            'quantity', 'price', 'subtotal', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'subtotal')


class CartSerializer(serializers.ModelSerializer):
    """Cart serializer"""
    items = CartItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = (
            'id', 'customer_id', 'items', 'items_count',
            'total', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'customer_id', 'created_at', 'updated_at', 'total')

    def get_items_count(self, obj):
        return obj.items.count()


class RefundSerializer(serializers.ModelSerializer):
    """Refund serializer"""

    class Meta:
        model = Refund
        fields = (
            'id', 'order', 'order_item_id', 'customer_id',
            'reason', 'status', 'refund_amount', 'processing_notes',
            'created_at', 'updated_at', 'processed_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
