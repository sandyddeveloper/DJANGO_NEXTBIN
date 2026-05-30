"""
Utility functions and helpers.
"""

import logging
from functools import wraps
from django.utils.decorators import decorator_from_middleware
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def log_api_call(view_func):
    """Decorator to log API calls."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        import time
        start_time = time.time()
        
        try:
            response = view_func(request, *args, **kwargs)
            duration = (time.time() - start_time) * 1000
            
            # Log the call
            from apps.core.models import APILog
            APILog.objects.create(
                endpoint=request.path,
                method=request.method,
                status_code=response.status_code,
                response_time_ms=int(duration),
                user=request.user if request.user.is_authenticated else None,
                ip_address=get_client_ip(request)
            )
            
            return response
        except Exception as e:
            logger.exception(f"Error in {view_func.__name__}: {str(e)}")
            raise
    
    return wrapper


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def is_ajax(request):
    """Check if request is AJAX."""
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


def get_pagination_params(request):
    """Extract pagination parameters from request."""
    page = request.query_params.get('page', 1)
    page_size = request.query_params.get('page_size', 20)
    
    try:
        page = int(page)
        page_size = int(page_size)
        page = max(page, 1)
        page_size = max(page_size, 1)
        page_size = min(page_size, 100)  # Max 100 items per page
    except (ValueError, TypeError):
        page = 1
        page_size = 20
    
    return page, page_size


def format_error_response(message, error_code='ERROR', status_code=status.HTTP_400_BAD_REQUEST):
    """Format error response."""
    return Response(
        {
            'error': error_code,
            'message': message,
            'status': 'error'
        },
        status=status_code
    )


def format_success_response(data, message='Success', status_code=status.HTTP_200_OK):
    """Format success response."""
    return Response(
        {
            'data': data,
            'message': message,
            'status': 'success'
        },
        status=status_code
    )
