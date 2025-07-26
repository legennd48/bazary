"""
Core views for health checks and utilities.
"""

from django.http import JsonResponse
from django.utils import timezone
from django.db import connections
from django.core.cache import cache


def health_check(request):
    """
    Health check endpoint to verify system status.
    """
    health_status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'services': {}
    }
    
    # Database check
    try:
        db_conn = connections['default']
        with db_conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['services']['database'] = 'healthy'
    except Exception as e:
        health_status['services']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Cache check (if Redis is configured)
    try:
        cache.get('health_check')
        health_status['services']['cache'] = 'healthy'
    except Exception as e:
        health_status['services']['cache'] = f'degraded: {str(e)}'
        if health_status['status'] == 'healthy':
            health_status['status'] = 'degraded'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)
