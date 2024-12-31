# products/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .models import Product
from .serializers import ProductSerializer
from django_filters import rest_framework as filters
from core.permissions import IsAdminOrReadOnly
from django.utils import timezone
from rabbitmq.handler import RabbitMQHandler
import logging

logger = logging.getLogger(__name__)

class CustomPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    max_page_size = 100

class ProductFilter(filters.FilterSet):
    category = filters.NumberFilter(field_name='category__id')
    animalType = filters.CharFilter(field_name='animal_type')
    
    class Meta:
        model = Product
        fields = ['category', 'animal_type']


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    pagination_class = CustomPageNumberPagination
    permission_classes = [IsAdminOrReadOnly]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.rabbitmq_handler = RabbitMQHandler()
            self.rabbitmq_handler.setup_connection()
            logger.info("Successfully connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            self.rabbitmq_handler = None

    def get_queryset(self):
        return Product.objects.all()

    def perform_create(self, serializer):
        try:
            product = serializer.save()
            message = {
                'event': 'product_created',
                'product_id': product.id,
                'name': product.name,
                'description': product.description,
                'price': str(product.price),  # Convert Decimal to string for JSON
                'category_id': product.category.id if product.category else None,
                'animal_type': product.animal_type,
                'timestamp': timezone.now().isoformat(),
            }
            logger.info(f"Product created, preparing to publish message: {message}")

            self.rabbitmq_handler.publish(
                'product_events',
                'product.created',
                message
            )
        except Exception as e:
            logger.error(f"Error in perform_create: {str(e)}", exc_info=True)
            raise

    def perform_update(self, serializer):
        try:
            product = serializer.save()
            message = {
                'event': 'product_updated',
                'product_id': product.id,
                'name': product.name,
                'description': product.description,
                'price': str(product.price),
                'category_id': product.category.id if product.category else None,
                'animal_type': product.animal_type,
                'timestamp': timezone.now().isoformat(),
            }
            logger.info(f"Product updated, preparing to publish message: {message}")

            self.rabbitmq_handler.publish(
                'product_events',
                'product.updated',
                message
            )
        except Exception as e:
            logger.error(f"Error in perform_update: {e}", exc_info=True)
            raise

    def perform_destroy(self, instance):
        try:
            product_id = instance.id
            message = {
                'event': 'product_deleted',
                'product_id': product_id,
                'timestamp': timezone.now().isoformat(),
            }
            logger.info(f"Product deleted, preparing to publish message: {message}")

            self.rabbitmq_handler.publish(
                'product_events',
                'product.deleted',
                message
            )
            instance.delete()
        except Exception as e:
            logger.error(f"Error in perform_destroy: {e}", exc_info=True)
            raise