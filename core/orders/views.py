# orders/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Order
from .serializers import OrderSerializer
from core.permissions import IsOwnerOrAdmin  
from rabbitmq.handler import RabbitMQHandler
from django.utils import timezone

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rabbitmq_handler = RabbitMQHandler()

    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        order = serializer.save(user=self.request.user)
        
        # Publish order created event
        self.rabbitmq_handler.publish(
            'order_events',
            'order.created',
            {
                'event': 'order_created',
                'order_id': order.id,
                'user_id': order.user.id,
                'items': [
                    {
                        'product_id': item.product.id,
                        'quantity': item.quantity,
                        'price': str(item.price)
                    }
                    for item in order.items.all()
                ],
                'status': order.status,
                'total': str(order.total),
                'timestamp': timezone.now().isoformat()
            }
        )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status == 'pending':
            order.status = 'cancelled'
            order.save()
            
            # Publish order cancelled event
            self.rabbitmq_handler.publish(
                'order_events',
                'order.cancelled',
                {
                    'event': 'order_cancelled',
                    'order_id': order.id,
                    'user_id': order.user.id,
                    'items': [
                        {
                            'product_id': item.product.id,
                            'quantity': item.quantity,
                            'price': str(item.price)
                        }
                        for item in order.items.all()
                    ],
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            return Response({'status': 'order cancelled'})
        return Response(
            {'error': 'Order cannot be cancelled'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    def perform_update(self, serializer):
        order = serializer.save()
        
        # Publish order updated event
        self.rabbitmq_handler.publish(
            'order_events',
            'order.updated',
            {
                'event': 'order_updated',
                'order_id': order.id,
                'user_id': order.user.id,
                'items': [
                    {
                        'product_id': item.product.id,
                        'quantity': item.quantity,
                        'price': str(item.price)
                    }
                    for item in order.items.all()
                ],
                'status': order.status,
                'total': str(order.total),
                'timestamp': timezone.now().isoformat()
            }
        )