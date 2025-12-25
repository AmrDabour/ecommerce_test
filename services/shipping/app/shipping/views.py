from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import ShippingMethod, Shipment, ReturnRequest
from .serializers import ShippingMethodSerializer, ShipmentSerializer, ReturnRequestSerializer


class ShippingMethodViewSet(viewsets.ReadOnlyModelViewSet):
    """Shipping methods - public"""
    queryset = ShippingMethod.objects.filter(is_active=True)
    serializer_class = ShippingMethodSerializer
    permission_classes = [AllowAny]


class ShipmentViewSet(viewsets.ReadOnlyModelViewSet):
    """Shipment tracking"""
    queryset = Shipment.objects.all()
    serializer_class = ShipmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Customers see shipments for their orders
        # This would need to call Order service to verify ownership
        return super().get_queryset()


class ReturnRequestViewSet(viewsets.ModelViewSet):
    """Return requests"""
    queryset = ReturnRequest.objects.all()
    serializer_class = ReturnRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Customers see only their returns
        return super().get_queryset().filter(customer_id=self.request.user.id)
