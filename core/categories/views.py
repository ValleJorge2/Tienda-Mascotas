from rest_framework import viewsets
from .models import Category
from .serializers import CategorySerializer
from core.permissions import IsAdminOrReadOnly
from django.utils import timezone
from rabbitmq.handler import RabbitMQHandler
import logging

logger = logging.getLogger(__name__)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.rabbitmq_handler = RabbitMQHandler()
            # Test the connection
            self.rabbitmq_handler.setup_connection()
            logger.info("Successfully connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            self.rabbitmq_handler = None

    def perform_create(self, serializer):
        logger.info("Starting category creation...")
        try:
            category = serializer.save()
            logger.info(f"Category saved: ID={category.id}, Name={category.name}")
            
            message = {
                'event': 'category_created',
                'category_id': category.id,
                'name': category.name,
                'description': category.description,
                'timestamp': timezone.now().isoformat(),
            }
            logger.info(f"Attempting to publish message: {message}")
            
            self.rabbitmq_handler.publish(
                'category_events',
                'category.created',
                message
            )
            logger.info("Successfully published category created event")
        except Exception as e:
            logger.error(f"Error in perform_create: {str(e)}", exc_info=True)
            raise

    def perform_update(self, serializer):
        try:
            category = serializer.save()
            message = {
                'event': 'category_updated',
                'category_id': category.id,
                'name': category.name,
                'description': category.description,
                'timestamp': timezone.now().isoformat(),
            }
            logger.info(f"Category updated, preparing to publish message: {message}")
            
            self.rabbitmq_handler.publish(
                'category_events',
                'category.updated',  # Use specific routing key
                message
            )
        except Exception as e:
            logger.error(f"Error in perform_update: {e}", exc_info=True)
            raise