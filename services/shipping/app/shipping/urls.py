from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ShippingMethodViewSet,
    ShipmentViewSet,
    ReturnRequestViewSet,
)

app_name = 'shipping'

router = DefaultRouter()
router.register(r'methods', ShippingMethodViewSet, basename='method')
router.register(r'shipments', ShipmentViewSet, basename='shipment')
router.register(r'returns', ReturnRequestViewSet, basename='return')

urlpatterns = [
    path('', include(router.urls)),
]
