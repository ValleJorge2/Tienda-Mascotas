# cart/management/commands/cart_product_consumer.py
from django.core.management.base import BaseCommand
from rabbitmq.handler import RabbitMQHandler
import json
import logging

logger = logging.getLogger(__name__)

def handle_message_callback(command_instance, ch, method, properties, body):
    logger.info('=' * 50)
    logger.info(f'Message received on {method.routing_key}')
    logger.info(f'Body: {body}')
    logger.info('=' * 50)
    
    try:
        message = json.loads(body) if isinstance(body, bytes) else body
        command_instance.handle_message(message)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info('Successfully processed message')
    except Exception as e:
        logger.error(f'Error processing message: {e}')
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

class Command(BaseCommand):
    help = 'Starts the RabbitMQ consumer for product events in Cart service'

    def handle_message(self, message):
        event_type = message.get('event')
        if event_type == 'product_updated':
            self.stdout.write(
                self.style.SUCCESS(
                    f'📝 Product updated in Cart service:\n'
                    f'   ID: {message.get("product_id")}\n'
                    f'   Name: {message.get("name")}\n'
                    f'   Price: {message.get("price")}\n'
                    f'   Category: {message.get("category_id")}'
                )
            )
        elif event_type == 'product_deleted':
            self.stdout.write(
                self.style.SUCCESS(
                    f'🗑️ Product deleted from Cart service:\n'
                    f'   ID: {message.get("product_id")}'
                )
            )
        elif event_type == 'product_created':
            self.stdout.write(
                self.style.SUCCESS(
                    f'✨ New product available in Cart service:\n'
                    f'   ID: {message.get("product_id")}\n'
                    f'   Name: {message.get("name")}\n'
                    f'   Price: {message.get("price")}\n'
                    f'   Category: {message.get("category_id")}'
                )
            )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Starting Cart Product Consumer...'))
        
        handler = RabbitMQHandler()
        
        try:
            exchange_name = 'product_events'
            queue_name = 'cart.product_events'
            routing_key = 'product.*'

            handler.setup_consumer(queue_name, exchange_name, routing_key)
            
            from functools import partial
            callback = partial(handle_message_callback, self)
            
            handler._channel.basic_qos(prefetch_count=1)
            handler._channel.basic_consume(
                queue=queue_name,
                on_message_callback=callback,
                auto_ack=False
            )
            
            logger.info('👂 Listening for product events...')
            handler._channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info('Stopping consumer...')
            if handler._connection and not handler._connection.is_closed:
                handler._connection.close()
        except Exception as e:
            logger.error(f'Error: {e}', exc_info=True)
            if handler._connection and not handler._connection.is_closed:
                handler._connection.close()
            raise