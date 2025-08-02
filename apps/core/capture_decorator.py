"""
Decorator for capturing API responses for Swagger documentation.
"""

from functools import wraps
from .response_capture import response_capture


def capture_for_swagger(endpoint_name):
    """
    Decorator to capture API responses for Swagger examples.
    
    Usage:
        @capture_for_swagger('user_register')
        def post(self, request):
            # Your view logic
            return Response(data)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            # Get request object (could be in args[1] for class methods)
            request = None
            if len(args) > 1 and hasattr(args[1], 'method'):
                request = args[1]
            elif len(args) > 0 and hasattr(args[0], 'method'):
                request = args[0]
            
            # Execute the original view
            response = view_func(*args, **kwargs)
            
            # Capture the response if we have a request
            if request and hasattr(response, 'status_code'):
                response_capture.capture_response(
                    request, response, endpoint_name, request.method
                )
            
            return response
        return wrapper
    return decorator


def load_captured_examples():
    """
    Load all captured examples for use in Swagger documentation.
    
    Returns:
        dict: Examples organized by endpoint
    """
    return response_capture.load_examples_for_swagger()


def get_example_for_endpoint(endpoint_name, method, status_code):
    """
    Get a specific captured example.
    
    Args:
        endpoint_name: The endpoint name
        method: HTTP method
        status_code: HTTP status code
        
    Returns:
        dict: Example data or None
    """
    example = response_capture.get_example(endpoint_name, method, status_code)
    return example['response_data'] if example else None
