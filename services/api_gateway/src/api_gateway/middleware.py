import uuid
import logging


class CorrelationIdMiddleware:
    """Middleware to add correlation ID to requests for tracing"""

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger(__name__)

    def __call__(self, request):
        # Generate or get correlation ID
        correlation_id = request.META.get('HTTP_X_CORRELATION_ID') or str(uuid.uuid4())

        # Add to request META for use in views
        request.META['X_CORRELATION_ID'] = correlation_id

        # Add to logging context
        extra = {'correlation_id': correlation_id}
        self.logger.info(f"Request started: {request.method} {request.path}", extra=extra)

        # Process the request
        response = self.get_response(request)

        # Add correlation ID to response headers
        response['X-Correlation-ID'] = correlation_id

        self.logger.info(f"Request completed: {response.status_code}", extra=extra)

        return response
