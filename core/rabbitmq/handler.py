import pika
import json
import logging
import os
import threading

logger = logging.getLogger(__name__)

class RabbitMQHandler:
    _instance = None
    _connection = None
    _channel = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RabbitMQHandler, cls).__new__(cls)
            return cls._instance

    def __init__(self):
        self.host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
        if not self._connection or not self._channel:
            self.setup_connection()

    # core/rabbitmq/handler.py

    def setup_connection(self):
        try:
            if not self._connection or self._connection.is_closed:
                credentials = pika.PlainCredentials('guest', 'guest')
                parameters = pika.ConnectionParameters(
                    host=self.host,
                    credentials=credentials,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
                self._connection = pika.BlockingConnection(parameters)
                self._channel = self._connection.channel()

                # Declare exchange
                self._channel.exchange_declare(
                    exchange='category_events',
                    exchange_type='topic',
                    durable=True
                )

                # Declare all queues
                queues = ['products.events', 'cart.events', 'reviews.events', 'categories.events']
                for queue in queues:
                    self._channel.queue_declare(queue=queue, durable=True)
                    self._channel.queue_bind(
                        exchange='category_events',
                        queue=queue,
                        routing_key='category.*'
                    )

                logger.info("Successfully established RabbitMQ connection and declared queues")
        except Exception as e:
            logger.error(f"Error connecting to RabbitMQ: {str(e)}", exc_info=True)
            raise

    def ensure_connection(self):
        if not self._connection or self._connection.is_closed:
            self.setup_connection()

    def publish(self, exchange, routing_key, message):
        try:
            self.ensure_connection()
            logger.info(f"About to publish to exchange: {exchange} with routing key: {routing_key}")

            self._channel.exchange_declare(
                exchange=exchange,
                exchange_type='topic',
                durable=True
            )

            message_body = json.dumps(message).encode() if isinstance(message, dict) else message
            
            self._channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                ),
                mandatory=True  # Ensure message is routed to at least one queue
            )
            logger.info(f"Message published successfully: {message}")
        except Exception as e:
            logger.error(f"Error publishing message: {str(e)}", exc_info=True)
            self.setup_connection()  # Try to reconnect
            raise

    def setup_queue(self, queue_name, exchange='category_events', routing_key='category.*'):
        logger.info(f"Starting queue setup for {queue_name}")
        try:
            self.ensure_connection()

            logger.info(f"Declaring exchange {exchange}")
            self._channel.exchange_declare(
                exchange=exchange,
                exchange_type='topic',
                durable=True
            )

            logger.info(f"Declaring queue {queue_name}")
            result = self._channel.queue_declare(
                queue=queue_name,
                durable=True
            )
            logger.info(f"Queue {queue_name} declared with {result.method.message_count} messages waiting")

            logger.info(f"Binding {queue_name} to {exchange} with key {routing_key}")
            self._channel.queue_bind(
                exchange=exchange,
                queue=queue_name,
                routing_key=routing_key
            )
            logger.info("Queue setup completed successfully")
        except Exception as e:
            logger.error(f"Error in queue setup: {e}", exc_info=True)
            raise

    def consume(self, queue_name, callback, routing_key='category.*'):
        try:
            self.ensure_connection()
            self._channel.basic_qos(prefetch_count=1)
            self._channel.basic_consume(
                queue=queue_name,
                on_message_callback=callback,
                auto_ack=False
            )
            logger.info(f"Started consuming from {queue_name}")
            self._channel.start_consuming()
        except Exception as e:
            logger.error(f"Error in consumer: {e}", exc_info=True)
            raise
    
    
    def setup_consumer(self, queue_name, exchange, routing_key):
        logger.info(f"Setting up consumer for queue: {queue_name}")
        try:
            self.setup_connection()
            
            # Declare the exchange
            self._channel.exchange_declare(
                exchange=exchange,
                exchange_type='topic',
                durable=True
            )
            
            # Declare the queue with the correct name
            result = self._channel.queue_declare(
                queue=queue_name,
                durable=True
            )
            logger.info(f"Queue {queue_name} declared with {result.method.message_count} messages waiting")

            # For product events, bind to product.* routing keys
            if 'product' in exchange:
                routing_keys = ['product.created', 'product.updated', 'product.deleted']
            else:
                routing_keys = ['category.created', 'category.updated', 'category.deleted']
            
            for key in routing_keys:
                self._channel.queue_bind(
                    exchange=exchange,
                    queue=queue_name,
                    routing_key=key
                )
                logger.info(f"Queue {queue_name} bound to exchange {exchange} with key {key}")
            
        except Exception as e:
            logger.error(f"Error setting up consumer: {e}", exc_info=True)
            raise

    def handle_message_callback(command_instance, ch, method, properties, body):
        logger.info('=' * 50)
        logger.info(f'Message received on {method.routing_key}')
        logger.info(f'Body: {body}')
        logger.info('=' * 50)
        
        try:
            message = json.loads(body.decode()) if isinstance(body, bytes) else body
            logger.info(f"Decoded message: {message}")
            command_instance.handle_message(message)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info('Successfully processed message')
        except Exception as e:
            logger.error(f'Error processing message: {e}', exc_info=True)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)