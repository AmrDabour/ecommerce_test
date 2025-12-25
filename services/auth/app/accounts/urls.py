from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VendorProfileViewSet, CustomerProfileViewSet, AddressViewSet

app_name = 'accounts'

router = DefaultRouter()
router.register(r'vendors', VendorProfileViewSet, basename='vendor')
router.register(r'customers', CustomerProfileViewSet, basename='customer')
router.register(r'addresses', AddressViewSet, basename='address')

urlpatterns = [
    path('', include(router.urls)),
]
