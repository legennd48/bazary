"""
Response capture system for automatic Swagger example generation.
"""

import json
import os
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.http import JsonResponse

from rest_framework.response import Response


class ResponseCapture:
    """Captures API responses and saves them as Swagger examples."""

    def __init__(self):
        self.examples_dir = Path(settings.BASE_DIR) / "swagger_examples"
        self.examples_dir.mkdir(exist_ok=True)

    def capture_response(self, request, response, endpoint_name, method):
        """
        Capture a response and save it as an example.

        Args:
            request: Django request object
            response: DRF Response object
            endpoint_name: Name of the endpoint (e.g., 'user_register')
            method: HTTP method (GET, POST, PUT, DELETE)
        """
        if not isinstance(response, (Response, JsonResponse)):
            return

        # Extract response data
        if hasattr(response, "data"):
            response_data = response.data
        elif hasattr(response, "content"):
            try:
                response_data = json.loads(response.content.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return
        else:
            return

        # Create example structure
        example = {
            "endpoint": endpoint_name,
            "method": method.upper(),
            "status_code": response.status_code,
            "timestamp": datetime.now().isoformat(),
            "request_data": self._extract_request_data(request),
            "response_data": response_data,
            "headers": dict(response._headers) if hasattr(response, "_headers") else {},
        }

        # Save to file (only if not in DEBUG mode to avoid permission issues)
        from django.conf import settings

        if not getattr(settings, "DEBUG", False):
            filename = f"{endpoint_name}_{method.lower()}_{response.status_code}.json"
            filepath = self.examples_dir / filename

            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(example, f, indent=2, default=str, ensure_ascii=False)
            except (PermissionError, OSError) as e:
                # Silently ignore file writing errors in development
                pass

    def _extract_request_data(self, request):
        """Extract relevant request data."""
        request_data = {}

        if hasattr(request, "data") and request.data:
            request_data = dict(request.data)
            # Remove sensitive data
            sensitive_fields = ["password", "password_confirm", "token"]
            for field in sensitive_fields:
                if field in request_data:
                    request_data[field] = "***HIDDEN***"

        return request_data

    def get_example(self, endpoint_name, method, status_code):
        """
        Get saved example for an endpoint.

        Args:
            endpoint_name: Name of the endpoint
            method: HTTP method
            status_code: HTTP status code

        Returns:
            dict: Example data or None if not found
        """
        filename = f"{endpoint_name}_{method.lower()}_{status_code}.json"
        filepath = self.examples_dir / filename

        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def load_examples_for_swagger(self):
        """
        Load all captured examples for Swagger documentation.

        Returns:
            dict: Organized examples by endpoint and status code
        """
        examples = {}

        for file_path in self.examples_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    example = json.load(f)

                endpoint = example["endpoint"]
                method = example["method"]
                status_code = example["status_code"]

                if endpoint not in examples:
                    examples[endpoint] = {}
                if method not in examples[endpoint]:
                    examples[endpoint][method] = {}

                examples[endpoint][method][status_code] = {
                    "description": f"Captured response from {example['timestamp']}",
                    "value": example["response_data"],
                }

            except (json.JSONDecodeError, KeyError):
                continue

        return examples


# Global instance
response_capture = ResponseCapture()


def capture_response_middleware(get_response):
    """
    Middleware to automatically capture responses for documentation.
    """

    def middleware(request):
        response = get_response(request)

        # Only capture API responses
        if request.path.startswith("/api/"):
            # Extract endpoint name from path
            path_parts = request.path.strip("/").split("/")
            if len(path_parts) >= 3:  # ['api', 'v1', 'endpoint']
                endpoint_name = "_".join(path_parts[2:])
                response_capture.capture_response(
                    request, response, endpoint_name, request.method
                )

        return response

    return middleware
