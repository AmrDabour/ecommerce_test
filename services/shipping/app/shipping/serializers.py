from rest_framework import serializers
from .models import ShippingMethod, Shipment, ShipmentTracking, ReturnRequest


class ShippingMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingMethod
        fields = '__all__'


class ShipmentTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentTracking
        fields = '__all__'


class ShipmentSerializer(serializers.ModelSerializer):
    tracking = ShipmentTrackingSerializer(many=True, read_only=True)
    class Meta:
        model = Shipment
        fields = '__all__'


class ReturnRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnRequest
        fields = '__all__'
