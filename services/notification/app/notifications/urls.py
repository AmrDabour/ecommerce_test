from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationViewSet,
    NotificationPreferenceViewSet,
)

app_name = 'notifications'

router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')
router.register(r'preferences', NotificationPreferenceViewSet, basename='preference')

urlpatterns = [
    path('', include(router.urls)),
]
