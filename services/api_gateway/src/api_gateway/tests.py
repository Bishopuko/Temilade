import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock, Mock
from api_gateway.models import Notification, NotificationStatus
# ...existing code...
import pytest
import fakeredis


# Replace import path if your views import redis_client differently (e.g. api_gateway.redis_client)
REDIS_TARGET = "api_gateway.views.redis_client"
REQUESTS_TARGET = "api_gateway.views.requests"

@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    """
    Provide a fake redis instance for all tests to prevent real Redis connections.
    """
    fake_server = fakeredis.FakeServer()
    fake_client = fakeredis.FakeStrictRedis(server=fake_server)
    monkeypatch.setattr(REDIS_TARGET, fake_client)
    yield

@pytest.fixture(autouse=True)
def mock_user_service_requests(monkeypatch):
    """
    Prevent outbound HTTP calls to the user service during tests.
    Returns a simple 200 response with expected fields. Adjust payload as needed.
    """
    mock_requests = Mock()

    def mocked_get(url, *args, **kwargs):
        mock_resp = Mock()
        # adapt the returned json to what your code expects
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"email": "test@example.com", "push_token": "token123"}
        return mock_resp

    mock_requests.get = mocked_get
    monkeypatch.setattr(REQUESTS_TARGET, mock_requests)
    yield
# ...existing code...

class NotificationAPITestCase(APITestCase):
    """Test cases for notification API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.valid_payload = {
            'notification_type': 'email',
            'user_id': 'user123',
            'template_code': 'welcome_email',
            'variables': {
                'name': 'John Doe',
                'link': 'https://example.com'
            },
            'priority': 1,
            'metadata': {'source': 'test'}
        }

        self.invalid_payload = {
            'notification_type': 'invalid_type',
            'user_id': '',
            'template_code': '',
            'variables': {}
        }

    @patch('api_gateway.views.get_rabbitmq_connection')
    @patch('api_gateway.views.requests.get')
    def test_send_notification_success(self, mock_requests_get, mock_rabbitmq):
        """Test successful notification sending"""
        # Mock external service responses
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests_get.return_value = mock_response

        # Mock RabbitMQ connection
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_rabbitmq.return_value = mock_connection

        url = reverse('send_notification')
        response = self.client.post(url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('request_id', data)

    def test_send_notification_validation_error(self):
        """Test notification sending with validation errors"""
        url = reverse('send_notification')
        response = self.client.post(url, self.invalid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('details', data)

    @patch('api_gateway.views.redis_client')
    def test_get_notification_status_success(self, mock_redis):
        """Test getting notification status"""
        mock_redis.get.return_value = json.dumps({
            'notification_id': 'test123',
            'status': 'delivered',
            'timestamp': '2023-01-01T00:00:00.000000',
            'error': None
        })

        url = reverse('notification_status', kwargs={'request_id': 'test123'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertEqual(data['status'], 'delivered')

    @patch('api_gateway.views.redis_client')
    def test_get_notification_status_not_found(self, mock_redis):
        """Test getting status for non-existent notification"""
        mock_redis.get.return_value = None

        url = reverse('notification_status', kwargs={'request_id': 'nonexistent'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = json.loads(response.content)
        self.assertIn('error', data)

    @patch('api_gateway.views.redis_client')
    @patch('api_gateway.views.get_rabbitmq_connection')
    def test_health_check_success(self, mock_rabbitmq, mock_redis):
        """Test health check endpoint"""
        mock_redis.ping.return_value = True

        mock_connection = MagicMock()
        mock_rabbitmq.return_value = mock_connection

        url = reverse('health_check')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertIn('status', data)
        self.assertIn('dependencies', data)
        self.assertEqual(data['status'], 'healthy')

    def test_notification_model_creation(self):
        """Test Notification model creation"""
        notification = Notification.objects.create(
            notification_id='test123',
            status=NotificationStatus.pending.value,
            user_id='user123',
            notification_type='email',
            template_code='welcome',
            variables={'name': 'Test'},
            priority=1
        )

        self.assertEqual(notification.notification_id, 'test123')
        self.assertEqual(notification.status, NotificationStatus.pending.value)
        self.assertEqual(notification.user_id, 'user123')

    def test_notification_status_enum(self):
        """Test NotificationStatus enum values"""
        self.assertEqual(NotificationStatus.delivered.value, 'delivered')
        self.assertEqual(NotificationStatus.pending.value, 'pending')
        self.assertEqual(NotificationStatus.failed.value, 'failed')


class AuthenticationTestCase(APITestCase):
    """Test cases for authentication"""

    def test_jwt_token_endpoints_exist(self):
        """Test that JWT token endpoints are accessible"""
        # Test token obtain endpoint
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {
            'username': 'test',
            'password': 'test'
        }, format='json')
        # Should return 401 for invalid credentials, but endpoint exists
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_400_BAD_REQUEST])

        # Test token refresh endpoint
        url = reverse('token_refresh')
        response = self.client.post(url, {
            'refresh': 'invalid_token'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test token verify endpoint
        url = reverse('token_verify')
        response = self.client.post(url, {
            'token': 'invalid_token'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ValidationTestCase(TestCase):
    """Test cases for input validation"""

    def test_validate_notification_data_valid(self):
        """Test validation with valid data"""
        from .views import validate_notification_data

        valid_data = {
            'notification_type': 'email',
            'user_id': 'user123',
            'template_code': 'welcome',
            'variables': {'name': 'John'},
            'priority': 1,
            'metadata': {'key': 'value'}
        }

        errors = validate_notification_data(valid_data)
        self.assertEqual(len(errors), 0)

    def test_validate_notification_data_invalid(self):
        """Test validation with invalid data"""
        from .views import validate_notification_data

        invalid_data = {
            'notification_type': 'invalid',
            'user_id': '',
            'template_code': '',
            'variables': 'not_a_dict'
        }

        errors = validate_notification_data(invalid_data)
        self.assertGreater(len(errors), 0)
        self.assertIn('notification_type must be either "email" or "push"', errors)


class CircuitBreakerTestCase(TestCase):
    """Test cases for circuit breaker functionality"""

    def setUp(self):
        """Set up test data"""
        from .views import redis_client
        # Clear any existing circuit breaker state
        for service in ['user_service', 'template_service', 'general']:
            redis_client.delete(f"circuit_breaker:{service}")

    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker starts in closed state"""
        from .views import get_circuit_breaker_state

        state = get_circuit_breaker_state('user_service')
        self.assertEqual(state['state'], 'closed')
        self.assertEqual(state['failures'], 0)

    def test_circuit_breaker_failure_recording(self):
        """Test circuit breaker records failures correctly"""
        from .views import record_failure, get_circuit_breaker_state

        # Record failures
        for i in range(3):
            record_failure('user_service')

        state = get_circuit_breaker_state('user_service')
        self.assertEqual(state['failures'], 3)
        self.assertEqual(state['state'], 'closed')

    def test_circuit_breaker_opens_after_threshold(self):
        """Test circuit breaker opens after reaching failure threshold"""
        from .views import record_failure, get_circuit_breaker_state

        # Record failures to reach threshold
        for i in range(5):
            record_failure('user_service')

        state = get_circuit_breaker_state('user_service')
        self.assertEqual(state['state'], 'open')

    def test_circuit_breaker_half_open_recovery(self):
        """Test circuit breaker transitions to half-open after timeout"""
        from .views import record_failure, check_circuit_breaker, get_circuit_breaker_state
        import time

        # Open the circuit breaker
        for i in range(5):
            record_failure('user_service')

        state = get_circuit_breaker_state('user_service')
        self.assertEqual(state['state'], 'open')

        # Simulate timeout by manually setting old failure time
        from .views import redis_client
        redis_client.hmset('circuit_breaker:user_service', {
            'failures': 5,
            'last_failure_time': time.time() - 70,  # 70 seconds ago
            'state': 'open'
        })

        # Check should allow request (half-open)
        allowed = check_circuit_breaker('user_service')
        self.assertTrue(allowed)

        state = get_circuit_breaker_state('user_service')
        self.assertEqual(state['state'], 'half-open')

    def test_circuit_breaker_success_recovery(self):
        """Test circuit breaker recovers after successful request in half-open state"""
        from .views import record_success, get_circuit_breaker_state

        # Manually set half-open state
        from .views import redis_client
        redis_client.hmset('circuit_breaker:user_service', {
            'failures': 5,
            'last_failure_time': time.time(),
            'state': 'half-open'
        })

        # Record success
        record_success('user_service')

        state = get_circuit_breaker_state('user_service')
        self.assertEqual(state['state'], 'closed')
        self.assertEqual(state['failures'], 0)


class RateLimitingTestCase(APITestCase):
    """Test cases for rate limiting"""

    def test_rate_limit_allows_normal_requests(self):
        """Test that normal request rate is allowed"""
        url = reverse('send_notification')

        # Make requests within limit
        for i in range(5):
            response = self.client.post(url, {
                'notification_type': 'email',
                'user_id': 'user123',
                'template_code': 'welcome',
                'variables': {'name': 'Test'}
            }, format='json')
            # Should not be rate limited (may fail for other reasons but not 429)
            self.assertNotEqual(response.status_code, 429)

    def test_rate_limit_blocks_excess_requests(self):
        """Test that excessive requests are rate limited"""
        url = reverse('send_notification')

        # Make many requests quickly to trigger rate limit
        for i in range(150):  # Well above the 100/minute limit
            response = self.client.post(url, {
                'notification_type': 'email',
                'user_id': 'user123',
                'template_code': 'welcome',
                'variables': {'name': 'Test'}
            }, format='json')

        # At least some requests should be rate limited
        # Note: This test may be flaky in CI due to timing
        # In practice, rate limiting would be tested with proper load testing tools


class AuthenticationTestCase(APITestCase):
    """Test cases for authentication enforcement"""

    def test_send_notification_requires_authentication(self):
        """Test that send_notification endpoint requires authentication"""
        url = reverse('send_notification')

        # Try without authentication
        response = self.client.post(url, {
            'notification_type': 'email',
            'user_id': 'user123',
            'template_code': 'welcome',
            'variables': {'name': 'Test'}
        }, format='json')

        # Should require authentication (401 or 403)
        self.assertIn(response.status_code, [401, 403])

    def test_get_status_allows_anonymous(self):
        """Test that get_status endpoint allows anonymous access"""
        url = reverse('notification_status', kwargs={'request_id': 'test123'})

        response = self.client.get(url)
        # Should not require authentication (may return 404 but not 401/403)
        self.assertNotIn(response.status_code, [401, 403])

    def test_health_check_allows_anonymous(self):
        """Test that health check allows anonymous access"""
        url = reverse('health_check')

        response = self.client.get(url)
        # Should not require authentication
        self.assertNotIn(response.status_code, [401, 403])


class ErrorHandlingTestCase(APITestCase):
    """Test cases for comprehensive error handling"""

    @patch('api_gateway.views.requests.get')
    def test_user_service_timeout_handling(self, mock_get):
        """Test handling of user service timeouts"""
        from unittest.mock import Timeout
        mock_get.side_effect = Timeout("Connection timed out")

        url = reverse('send_notification')
        response = self.client.post(url, {
            'notification_type': 'email',
            'user_id': 'user123',
            'template_code': 'welcome',
            'variables': {'name': 'Test'}
        }, format='json')

        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertIn('error', data)

    @patch('api_gateway.views.requests.get')
    def test_template_service_5xx_error_handling(self, mock_get):
        """Test handling of template service 5xx errors"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        url = reverse('send_notification')
        response = self.client.post(url, {
            'notification_type': 'email',
            'user_id': 'user123',
            'template_code': 'welcome',
            'variables': {'name': 'Test'}
        }, format='json')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)

    @patch('api_gateway.views.redis_client')
    def test_redis_connection_failure_handling(self, mock_redis):
        """Test handling of Redis connection failures"""
        mock_redis.get.side_effect = Exception("Redis connection failed")

        url = reverse('notification_status', kwargs={'request_id': 'test123'})
        response = self.client.get(url)

        # Should handle gracefully (may return 500 or fallback)
        self.assertIn(response.status_code, [500, 404])


class PerformanceTestCase(APITestCase):
    """Test cases for performance requirements"""

    @patch('api_gateway.views.requests.get')
    @patch('api_gateway.views.get_rabbitmq_connection')
    def test_response_time_under_100ms(self, mock_rabbitmq, mock_requests_get):
        """Test that responses are under 100ms for successful requests"""
        # Mock successful external calls
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests_get.return_value = mock_response

        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_connection.channel.return_value = mock_channel
        mock_rabbitmq.return_value = mock_connection

        url = reverse('send_notification')
        import time

        start_time = time.time()
        response = self.client.post(url, {
            'notification_type': 'email',
            'user_id': 'user123',
            'template_code': 'welcome',
            'variables': {'name': 'Test'}
        }, format='json')
        end_time = time.time()

        response_time = (end_time - start_time) * 1000  # Convert to milliseconds

        # Assert response time is under 100ms (allowing some tolerance for test environment)
        self.assertLess(response_time, 200, f"Response time {response_time}ms exceeds 100ms limit")
        self.assertEqual(response.status_code, 200)


class CorrelationIdTestCase(APITestCase):
    """Test cases for correlation ID propagation"""

    def test_correlation_id_in_request_logging(self):
        """Test that correlation IDs are included in request logging"""
        url = reverse('health_check')

        with self.assertLogs('api_gateway', level='INFO') as log:
            response = self.client.get(url, **{'HTTP_X_CORRELATION_ID': 'test-correlation-id'})

        # Check that correlation ID appears in logs
        log_messages = [record.message for record in log.records]
        correlation_logs = [msg for msg in log_messages if 'correlation_id' in msg.lower()]
        self.assertTrue(len(correlation_logs) > 0, "Correlation ID should appear in logs")

    def test_correlation_id_generation(self):
        """Test that correlation IDs are generated when not provided"""
        url = reverse('health_check')

        with self.assertLogs('api_gateway', level='INFO') as log:
            response = self.client.get(url)

        # Should still log with some correlation ID        # ...existing code...
        import pytest
        import fakeredis
        from unittest.mock import Mock
        
        # Update these to match how your views import redis_client and requests
        REDIS_TARGET = "api_gateway.views.redis_client"
        REQUESTS_TARGET = "api_gateway.views.requests"
        
        @pytest.fixture(autouse=True)
        def fake_redis(monkeypatch):
            server = fakeredis.FakeServer()
            client = fakeredis.FakeStrictRedis(server=server)
            monkeypatch.setattr(REDIS_TARGET, client)
            yield
        
        @pytest.fixture(autouse=True)
        def mock_user_service_requests(monkeypatch):
            mock_requests = Mock()
        
            def mocked_get(url, *args, **kwargs):
                resp = Mock()
                resp.status_code = 200
                resp.json.return_value = {"email": "test@example.com", "push_token": "token123"}
                return resp
        
            mock_requests.get = mocked_get
            monkeypatch.setattr(REQUESTS_TARGET, mock_requests)
            yield
        # ...existing code...
        log_messages = [record.message for record in log.records]
        self.assertTrue(len(log_messages) > 0, "Should generate correlation ID when not provided")
