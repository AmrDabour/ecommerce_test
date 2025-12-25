from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet,
    CategoryViewSet,
    BrandViewSet,
    ProductReviewViewSet,
    WishlistViewSet,
)

app_name = 'products'

router = DefaultRouter()
router.register(r'', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'brands', BrandViewSet, basename='brand')
router.register(r'reviews', ProductReviewViewSet, basename='review')
router.register(r'wishlist', WishlistViewSet, basename='wishlist')

urlpatterns = [
    path('', include(router.urls)),
]
