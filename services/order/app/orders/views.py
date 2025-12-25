from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import Order, OrderItem, Cart, CartItem, Refund, OrderStatus
from .serializers import (
    OrderListSerializer, OrderDetailSerializer,
    CartSerializer, CartItemSerializer,
    RefundSerializer
)


class OrderViewSet(viewsets.ModelViewSet):
    """
    Order CRUD and management
    - List: Customer's own orders
    - Retrieve: Order details
    - Create: Create order from cart
    """
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        return OrderDetailSerializer

    def get_queryset(self):
        # Customers see only their orders
        return super().get_queryset().filter(customer_id=self.request.user.id)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order"""
        order = self.get_object()

        if order.status not in [OrderStatus.PENDING, OrderStatus.PAID]:
            return Response(
                {'detail': 'Order cannot be cancelled at this stage'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = OrderStatus.CANCELLED
        order.save()

        return Response({'status': 'Order cancelled successfully'})


class CartViewSet(viewsets.ModelViewSet):
    """
    Shopping cart management
    """
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Get or create cart for current user
        Cart.objects.get_or_create(customer_id=self.request.user.id)
        return super().get_queryset().filter(customer_id=self.request.user.id)

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Add item to cart"""
        cart = self.get_object()
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        variant_id = request.data.get('variant_id')

        if not product_id:
            return Response(
                {'detail': 'product_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if item already exists
        cart_item = cart.items.filter(
            product_id=product_id,
            variant_id=variant_id
        ).first()

        if cart_item:
            cart_item.quantity += int(quantity)
            cart_item.save()
        else:
            CartItem.objects.create(
                cart=cart,
                product_id=product_id,
                variant_id=variant_id,
                quantity=quantity
            )

        return Response(CartSerializer(cart).data)

    @action(detail=True, methods=['post'])
    def remove_item(self, request, pk=None):
        """Remove item from cart"""
        cart = self.get_object()
        item_id = request.data.get('item_id')

        if not item_id:
            return Response(
                {'detail': 'item_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart.items.filter(id=item_id).delete()
        return Response(CartSerializer(cart).data)

    @action(detail=True, methods=['post'])
    def clear(self, request, pk=None):
        """Clear all items from cart"""
        cart = self.get_object()
        cart.items.all().delete()
        return Response({'status': 'Cart cleared'})


class RefundViewSet(viewsets.ModelViewSet):
    """Refund requests"""
    queryset = Refund.objects.all()
    serializer_class = RefundSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Customers see only their refunds
        return super().get_queryset().filter(customer_id=self.request.user.id)
