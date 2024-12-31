from django.core.management.base import BaseCommand
from rabbitmq.handler import RabbitMQHandler
import json
import logging

logger = logging.getLogger(__name__)

def handle_message_callback(command_instance, ch, method, properties, body):
    print('=' * 50)
    print(f'Message received on {method.routing_key}')
    print(f'Body: {body}')
    print('=' * 50)
    
    try:
        message = json.loads(body) if isinstance(body, bytes) else body
        command_instance.handle_message(message)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f'Successfully processed message')
    except Exception as e:
        print(f'Error processing message: {e}')
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

class Command(BaseCommand):
    help = 'Starts the RabbitMQ consumer for cart service'

    def handle_message(self, message):
        event_type = message.get('event')
        if event_type == 'category_updated':
            self.stdout.write(
                self.style.SUCCESS(
                    f'📝 Category updated in Cart service:\n'
                    f'   ID: {message.get("category_id")}\n'
                    f'   Name: {message.get("name")}\n'
                    f'   Description: {message.get("description")}'
                )
            )
        elif event_type == 'category_created':
            self.stdout.write(
                self.style.SUCCESS(
                    f'🆕 New category available in Cart:\n'
                    f'   ID: {message.get("category_id")}\n'
                    f'   Name: {message.get("name")}\n'
                    f'   Description: {message.get("description")}'
                )
            )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Starting Cart Consumer...'))
        
        handler = RabbitMQHandler()
        
        try:
            exchange_name = 'category_events'
            queue_name = 'cart.events'
            routing_key = 'category.*'
            
            handler.setup_consumer(queue_name, exchange_name, routing_key)
            
            from functools import partial
            callback = partial(handle_message_callback, self)
            
            handler._channel.basic_qos(prefetch_count=1)
            handler._channel.basic_consume(
                queue=queue_name,
                on_message_callback=callback,
                auto_ack=False
            )
            
            print('👂 Listening for category events...')
            handler._channel.start_consuming()
            
        except KeyboardInterrupt:
            print('Stopping consumer...')
            if handler._connection and not handler._connection.is_closed:
                handler._connection.close()
        except Exception as e:
            print(f'Error: {e}')
            if handler._connection and not handler._connection.is_closed:
                handler._connection.close()
            raise