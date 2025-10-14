#!/usr/bin/env python
"""
Script to check if Celery workers are running
"""
import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bazary.settings.development')
django.setup()

from bazary.celery import app
from celery.app.control import Control

def check_celery_workers():
    """Check if Celery workers are active"""
    print("🔍 Checking Celery worker status...")
    
    try:
        # Get active workers
        control = Control(app)
        active_workers = control.ping()
        
        if active_workers:
            print(f"✅ Found {len(active_workers)} active Celery worker(s):")
            for worker in active_workers:
                for worker_name, response in worker.items():
                    print(f"   - {worker_name}: {response}")
        else:
            print("❌ No active Celery workers found")
            
        return len(active_workers) > 0
        
    except Exception as e:
        print(f"❌ Error checking Celery workers: {e}")
        return False

def check_celery_broker():
    """Check if Celery broker is accessible"""
    print("\n🔍 Checking Celery broker connection...")
    
    try:
        # Test broker connection
        app.control.ping()
        print("✅ Celery broker is accessible")
        return True
    except Exception as e:
        print(f"❌ Cannot connect to Celery broker: {e}")
        return False

def check_celery_settings():
    """Display current Celery settings"""
    print("\n📋 Current Celery Configuration:")
    print(f"   Broker URL: {getattr(settings, 'CELERY_BROKER_URL', 'Not configured')}")
    print(f"   Result Backend: {getattr(settings, 'CELERY_RESULT_BACKEND', 'Not configured')}")
    print(f"   Task Always Eager: {getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', 'Not configured')}")
    print(f"   Timezone: {getattr(settings, 'CELERY_TIMEZONE', getattr(settings, 'TIME_ZONE', 'Not configured'))}")

if __name__ == "__main__":
    print("🚀 Celery Status Check")
    print("=" * 50)
    
    check_celery_settings()
    broker_ok = check_celery_broker()
    workers_ok = check_celery_workers()
    
    print("\n" + "=" * 50)
    if broker_ok and workers_ok:
        print("✅ Celery is running and ready!")
        sys.exit(0)
    elif broker_ok:
        print("⚠️  Celery broker is running but no workers found")
        print("💡 Start a worker with: celery -A bazary worker -l info")
        sys.exit(1)
    else:
        print("❌ Celery is not properly configured or running")
        sys.exit(1)