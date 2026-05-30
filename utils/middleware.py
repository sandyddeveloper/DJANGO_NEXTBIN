"""
Custom middleware for the application.
"""

import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(MiddlewareMixin):
    """Handle errors and log them."""
    
    def process_exception(self, request, exception):
        logger.exception(f"Exception in {request.method} {request.path}")
        return JsonResponse(
            {
                'error': 'An unexpected error occurred',
                'status': 'error'
            },
            status=500
        )


class RequestLoggingMiddleware(MiddlewareMixin):
    """Log all requests."""
    
    def process_request(self, request):
        logger.debug(f"{request.method} {request.path}")
        request.start_time = __import__('time').time()
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = __import__('time').time() - request.start_time
            logger.debug(f"{request.method} {request.path} - {response.status_code} ({duration:.2f}s)")
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security headers to responses."""
    
    def process_response(self, request, response):
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response
