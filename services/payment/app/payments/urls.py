from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentViewSet,
    CouponViewSet,
    VendorPayoutViewSet,
)

app_name = 'payments'

router = DefaultRouter()
router.register(r'', PaymentViewSet, basename='payment')
router.register(r'coupons', CouponViewSet, basename='coupon')
router.register(r'payouts', VendorPayoutViewSet, basename='payout')

urlpatterns = [
    path('', include(router.urls)),
]
