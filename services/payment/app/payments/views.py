from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from .models import Payment, VendorPayout, Coupon
from .serializers import PaymentSerializer, VendorPayoutSerializer, CouponSerializer


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """Payment views - read only for customers"""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().filter(customer_id=self.request.user.id)


class CouponViewSet(viewsets.ReadOnlyModelViewSet):
    """Coupon views - public list, admin management"""
    queryset = Coupon.objects.filter(is_active=True)
    serializer_class = CouponSerializer
    permission_classes = [AllowAny]


class VendorPayoutViewSet(viewsets.ReadOnlyModelViewSet):
    """Vendor payout views"""
    queryset = VendorPayout.objects.all()
    serializer_class = VendorPayoutSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Vendors see only their payouts
        if hasattr(self.request.user, 'vendor_profile'):
            return super().get_queryset().filter(vendor_id=self.request.user.id)
        return super().get_queryset().none()
