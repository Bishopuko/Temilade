import uuid
import json
import pika
import logging
import requests
import httpx
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
import redis
from django.core.cache import cache
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
import time
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from .models import Notification

class NotificationStatus(str, Enum):
    delivered = "delivered"
    pending = "pending"
    failed = "failed"

@dataclass
class NotificationStatusData:
    notification_id: str
    status: NotificationStatus
    timestamp: Optional[datetime] = None
    error: Optional[str] = None

# Setup logging
logger = logging.getLogger(__name__)

# RabbitMQ connection
def get_rabbitmq_connection():
    credentials = pika.PlainCredentials(
        settings.RABBITMQ_USER,
        settings.RABBITMQ_PASS
    )
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            settings.RABBITMQ_HOST,
            settings.RABBITMQ_PORT,
            '/',
            credentials
        )
    )
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

# Redis for idempotency and status tracking
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    decode_responses=True
)

# Circuit breaker state in Redis for multi-instance support
CIRCUIT_BREAKER_THRESHOLD = 5
CIRCUIT_BREAKER_TIMEOUT = 60  # seconds

def get_circuit_breaker_state(service_name):
    """Get circuit breaker state from Redis"""
    state = redis_client.hgetall(f"circuit_breaker:{service_name}")
    if not state:
        return {'failures': 0, 'last_failure_time': 0, 'state': 'closed'}
    return {
        'failures': int(state.get('failures', 0)),
        'last_failure_time': float(state.get('last_failure_time', 0)),
        'state': state.get('state', 'closed')
    }

def set_circuit_breaker_state(service_name, state):
    """Set circuit breaker state in Redis"""
    redis_client.hmset(f"circuit_breaker:{service_name}", state)

def check_circuit_breaker(service_name):
    """Check if circuit breaker allows the request"""
    state = get_circuit_breaker_state(service_name)
    current_time = time.time()

    if state['state'] == 'open':
        if current_time - state['last_failure_time'] > CIRCUIT_BREAKER_TIMEOUT:
            state['state'] = 'half-open'
            set_circuit_breaker_state(service_name, state)
            return True
        return False
    return True

def record_failure(service_name):
    """Record a failure in circuit breaker"""
    state = get_circuit_breaker_state(service_name)
    state['failures'] += 1
    state['last_failure_time'] = time.time()

    if state['failures'] >= CIRCUIT_BREAKER_THRESHOLD:
        state['state'] = 'open'

    set_circuit_breaker_state(service_name, state)

def record_success(service_name):
    """Record a success in circuit breaker"""
    state = get_circuit_breaker_state(service_name)
    if state['state'] == 'half-open':
        state['state'] = 'closed'
        state['failures'] = 0
        set_circuit_breaker_state(service_name, state)

def validate_notification_data(data):
    """Validate notification request data"""
    errors = []

    notification_type = data.get('notification_type')
    if not notification_type or notification_type not in ['email', 'push']:
        errors.append('notification_type must be either "email" or "push"')

    user_id = data.get('user_id')
    if not user_id or not isinstance(user_id, str):
        errors.append('user_id is required and must be a string')

    template_code = data.get('template_code')
    if not template_code or not isinstance(template_code, str):
        errors.append('template_code is required and must be a string')

    variables = data.get('variables', {})
    if not isinstance(variables, dict):
        errors.append('variables must be a dictionary')

    # Validate UserData structure
    if variables:
        if 'name' not in variables or not isinstance(variables['name'], str):
            errors.append('variables.name is required and must be a string')
        if 'link' in variables and not isinstance(variables['link'], str):
            errors.append('variables.link must be a valid URL string')
        if 'meta' in variables and not isinstance(variables['meta'], dict):
            errors.append('variables.meta must be a dictionary')

    request_id = data.get('request_id')
    if request_id and not isinstance(request_id, str):
        errors.append('request_id must be a string')

    priority = data.get('priority')
    if priority is not None and not isinstance(priority, int):
        errors.append('priority must be an integer')

    metadata = data.get('metadata')
    if metadata is not None and not isinstance(metadata, dict):
        errors.append('metadata must be a dictionary')

    return errors

@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='user', rate='100/m', block=True)
def send_notification(request):
    # Log request
    logger.info(f"Notification request from {request.META.get('REMOTE_ADDR')}")

    data = request.data

    # Validate input
    validation_errors = validate_notification_data(data)
    if validation_errors:
        logger.warning(f"Validation errors: {validation_errors}")
        return Response({
            'success': False,
            'error': 'Validation failed',
            'details': validation_errors
        }, status=status.HTTP_400_BAD_REQUEST)

    notification_type = data.get('notification_type')
    user_id = data.get('user_id')
    template_code = data.get('template_code')
    variables = data.get('variables', {})
    request_id = data.get('request_id')
    priority = data.get('priority', 1)
    metadata = data.get('metadata', {})

    # Check circuit breaker for user service
    if not check_circuit_breaker('user_service'):
        logger.warning("Circuit breaker is open for user service, rejecting request")
        return Response({
            'success': False,
            'error': 'Service temporarily unavailable'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # Use provided request_id or generate one
    if not request_id:
        request_fingerprint = f"{notification_type}:{user_id}:{template_code}:{json.dumps(variables, sort_keys=True)}"
        request_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, request_fingerprint))

    # Idempotency check
    if redis_client.get(f"idempotency:{request_id}"):
        logger.info(f"Duplicate request detected: {request_id}")
        return Response({
            'success': False,
            'error': 'Duplicate request',
            'request_id': request_id
        }, status=status.HTTP_409_CONFLICT)

    # Store initial status as structured data
    initial_status = NotificationStatusData(
        notification_id=request_id,
        status=NotificationStatus.pending,
        timestamp=datetime.now()
    )
    redis_client.setex(f"status:{request_id}", 3600, json.dumps({
        'notification_id': initial_status.notification_id,
        'status': initial_status.status.value,
        'timestamp': initial_status.timestamp.isoformat() if initial_status.timestamp else None,
        'error': initial_status.error
    }))
    redis_client.setex(f"idempotency:{request_id}", 3600, 'processing')

    try:
        # Validate user exists (circuit breaker protected)
        user_service_url = f"http://user_service:5000/users/{user_id}/contact"
        user_response = requests.get(user_service_url, timeout=5)

        if user_response.status_code != 200:
            record_failure('user_service')
            logger.error(f"User service error: {user_response.status_code}")
            return Response({
                'success': False,
                'error': 'User validation failed'
            }, status=status.HTTP_400_BAD_REQUEST)

        record_success('user_service')

        # Validate template exists (circuit breaker protected)
        template_service_url = f"http://template_service:8081/templates/{template_code}"
        template_response = requests.get(template_service_url, timeout=5)

        if template_response.status_code != 200:
            record_failure('template_service')
            logger.error(f"Template service error: {template_response.status_code}")
            return Response({
                'success': False,
                'error': 'Template validation failed'
            }, status=status.HTTP_400_BAD_REQUEST)

        record_success('template_service')

        # Publish to queue
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        setup_queues(channel)

        message = {
            'request_id': request_id,
            'user_id': user_id,
            'template_code': template_code,
            'variables': variables,
            'priority': priority,
            'metadata': metadata,
            'timestamp': time.time()
        }

        routing_key = f'{notification_type}.queue'
        channel.basic_publish(
            exchange='notifications.direct',
            routing_key=routing_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # persistent
                message_id=request_id
            )
        )
        connection.close()

        logger.info(f"Notification queued: {request_id}")
        return Response({
            'success': True,
            'message': 'Notification queued successfully',
            'request_id': request_id,
            'type': notification_type
        }, status=status.HTTP_200_OK)

    except Exception as e:
        record_failure('general')
        logger.error(f"Error processing notification: {str(e)}")
        # Store failed status with error details
        failed_status = NotificationStatusData(
            notification_id=request_id,
            status=NotificationStatus.failed,
            timestamp=datetime.now(),
            error=str(e)
        )
        redis_client.setex(f"status:{request_id}", 3600, json.dumps({
            'notification_id': failed_status.notification_id,
            'status': failed_status.status.value,
            'timestamp': failed_status.timestamp.isoformat() if failed_status.timestamp else None,
            'error': failed_status.error
        }))
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
@cache_page(60)  # Cache for 60 seconds
def get_notification_status(request, request_id):
    """Get the status of a notification by request_id"""
    if not request_id:
        return Response({
            'success': False,
            'error': 'request_id is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    status_json = redis_client.get(f"status:{request_id}")
    if not status_json:
        return Response({
            'success': False,
            'error': 'Notification not found'
        }, status=status.HTTP_404_NOT_FOUND)

    try:
        # Parse the JSON status data
        status_data = json.loads(status_json)
        return Response({
            'success': True,
            'notification_id': status_data['notification_id'],
            'status': status_data['status'],
            'timestamp': status_data.get('timestamp'),
            'error': status_data.get('error')
        }, status=status.HTTP_200_OK)
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Error parsing status data for {request_id}: {str(e)}")
        # Fallback for old format or corrupted data
        return Response({
            'success': True,
            'notification_id': request_id,
            'status': status_json,  # Return raw value
            'timestamp': time.time(),
            'error': None
        }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint"""
    # Check Redis connectivity
    try:
        redis_client.ping()
        redis_status = 'healthy'
    except:
        redis_status = 'unhealthy'

    # Check RabbitMQ connectivity
    try:
        connection = get_rabbitmq_connection()
        connection.close()
        rabbitmq_status = 'healthy'
    except:
        rabbitmq_status = 'unhealthy'

    overall_status = 'healthy' if redis_status == 'healthy' and rabbitmq_status == 'healthy' else 'degraded'

    return Response({
        'status': overall_status,
        'service': 'api_gateway',
        'dependencies': {
            'redis': redis_status,
            'rabbitmq': rabbitmq_status
        },
        'circuit_breaker': {
            'user_service': get_circuit_breaker_state('user_service')['state'],
            'template_service': get_circuit_breaker_state('template_service')['state'],
            'general': get_circuit_breaker_state('general')['state']
        },
        'timestamp': time.time()
    }, status=status.HTTP_200_OK)


# JWT Authentication Views
class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom token obtain view with additional logging"""
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        correlation_id = request.META.get('X_CORRELATION_ID')
        logger.info(f"Token obtain attempt", extra={'correlation_id': correlation_id})
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            logger.info(f"Token obtained successfully", extra={'correlation_id': correlation_id})
        else:
            logger.warning(f"Token obtain failed", extra={'correlation_id': correlation_id})
        return response


class CustomTokenRefreshView(TokenRefreshView):
    """Custom token refresh view with logging"""
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        correlation_id = request.META.get('X_CORRELATION_ID')
        logger.info(f"Token refresh attempt", extra={'correlation_id': correlation_id})
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            logger.info(f"Token refreshed successfully", extra={'correlation_id': correlation_id})
        else:
            logger.warning(f"Token refresh failed", extra={'correlation_id': correlation_id})
        return response


class CustomTokenVerifyView(TokenVerifyView):
    """Custom token verify view with logging"""
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        correlation_id = request.META.get('X_CORRELATION_ID')
        logger.info(f"Token verify attempt", extra={'correlation_id': correlation_id})
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            logger.info(f"Token verified successfully", extra={'correlation_id': correlation_id})
        else:
            logger.warning(f"Token verify failed", extra={'correlation_id': correlation_id})
        return response
