from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CartViewSet,
    OrderViewSet,
    RefundViewSet,
)

app_name = 'orders'

router = DefaultRouter()
router.register(r'', OrderViewSet, basename='order')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'refunds', RefundViewSet, basename='refund')

urlpatterns = [
    path('', include(router.urls)),
]
