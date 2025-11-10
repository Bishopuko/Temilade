import uuid
import json
import pika
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import redis

# RabbitMQ connection
def get_rabbitmq_connection():
    credentials = pika.PlainCredentials('admin', 'admin')
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', 5672, '/', credentials))
    return connection

# Setup RabbitMQ queues
def setup_queues(channel):
    # Declare exchange
    channel.exchange_declare(exchange='notifications.direct', exchange_type='direct')

    # Declare dead-letter exchange
    channel.exchange_declare(exchange='notifications.dlx', exchange_type='direct')

    # Declare failed queue (dead-letter queue)
    channel.queue_declare(queue='failed.queue', durable=True)
    channel.queue_bind(exchange='notifications.dlx', queue='failed.queue', routing_key='failed')

    # Declare email queue with dead-letter
    channel.queue_declare(queue='email.queue', durable=True, arguments={
        'x-dead-letter-exchange': 'notifications.dlx',
        'x-dead-letter-routing-key': 'failed'
    })
    channel.queue_bind(exchange='notifications.direct', queue='email.queue', routing_key='email.queue')

    # Declare push queue with dead-letter
    channel.queue_declare(queue='push.queue', durable=True, arguments={
        'x-dead-letter-exchange': 'notifications.dlx',
        'x-dead-letter-routing-key': 'failed'
    })
    channel.queue_bind(exchange='notifications.direct', queue='push.queue', routing_key='push.queue')

# Redis for idempotency
redis_client = redis.Redis(host='localhost', port=6379, db=0)

@api_view(['POST'])
def send_notification(request):
    data = request.data
    notification_type = data.get('type')  
    user_id = data.get('user_id')
    template_id = data.get('template_id')
    variables = data.get('variables', {})

    if not all([notification_type, user_id, template_id]):
        return Response({'success': False, 'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

    # Idempotency check
    request_id = str(uuid.uuid4())
    if redis_client.get(request_id):
        return Response({'success': False, 'error': 'Duplicate request'}, status=status.HTTP_409_CONFLICT)
    redis_client.set(request_id, 'processing', ex=3600)

    # Publish to queue
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    setup_queues(channel)

    message = {
        'request_id': request_id,
        'user_id': user_id,
        'template_id': template_id,
        'variables': variables,
    }

    routing_key = f'{notification_type}.queue'
    channel.basic_publish(exchange='notifications.direct', routing_key=routing_key, body=json.dumps(message))
    connection.close()

    return Response({'success': True, 'message': 'Notification queued', 'request_id': request_id}, status=status.HTTP_200_OK)

@api_view(['GET'])
def health_check(request):
    return Response({'status': 'healthy', 'service': 'api_gateway'}, status=status.HTTP_200_OK)
