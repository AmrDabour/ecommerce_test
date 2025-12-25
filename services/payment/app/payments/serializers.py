from rest_framework import serializers
from .models import Payment, PaymentRefund, VendorPayout, Coupon, CouponUsage, SavedPaymentMethod


class PaymentSerializer(serializers.ModelSerializer):
    """Payment serializer"""

    class Meta:
        model = Payment
        fields = (
            'id', 'payment_intent_id', 'order_id', 'customer_id',
            'amount', 'currency', 'status', 'payment_method',
            'payment_method_type', 'failure_reason',
            'created_at', 'updated_at', 'paid_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class CouponSerializer(serializers.ModelSerializer):
    """Coupon serializer"""

    class Meta:
        model = Coupon
        fields = (
            'id', 'code', 'description', 'discount_type', 'discount_value',
            'min_purchase_amount', 'max_discount_amount', 'usage_limit',
            'usage_count', 'is_active', 'valid_from', 'valid_until',
            'created_at'
        )
        read_only_fields = ('id', 'usage_count', 'created_at')


class VendorPayoutSerializer(serializers.ModelSerializer):
    """Vendor payout serializer"""

    class Meta:
        model = VendorPayout
        fields = (
            'id', 'vendor_id', 'order_id', 'amount', 'currency',
            'status', 'payout_method', 'transaction_id',
            'created_at', 'paid_at'
        )
        read_only_fields = ('id', 'created_at')


class SavedPaymentMethodSerializer(serializers.ModelSerializer):
    """Saved payment method serializer"""

    class Meta:
        model = SavedPaymentMethod
        fields = (
            'id', 'customer_id', 'stripe_payment_method_id',
            'payment_method_type', 'card_brand', 'card_last4',
            'card_exp_month', 'card_exp_year', 'is_default',
            'created_at'
        )
        read_only_fields = ('id', 'created_at')
