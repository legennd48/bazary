"""
ASGI config for bazary project.

Supports both HTTP and WebSocket protocols.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bazary.settings")

# Initialize Django ASGI application early to ensure settings are loaded
django_asgi_app = get_asgi_application()

# Import channels routing after Django setup
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

# Check if notifications capability is enabled
from apps.core.capabilities.registry import capabilities

if capabilities.is_enabled("notifications"):
    from apps.notifications.routing import websocket_urlpatterns
    
    application = ProtocolTypeRouter({
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            URLRouter(websocket_urlpatterns)
        ),
    })
else:
    # HTTP only if notifications disabled
    application = django_asgi_app
