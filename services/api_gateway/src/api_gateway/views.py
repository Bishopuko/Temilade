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

# Redis for idempotency
redis_client = redis.Redis(host='localhost', port=6379, db=0)

@api_view(['POST'])
def send_notification(request):
    data = request.data
    notification_type = data.get('type')  # 'email' or 'push'
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
    channel.exchange_declare(exchange='notifications.direct', exchange_type='direct')

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
    return Response({'status': 'healthy'}, status=status.HTTP_200_OK)
