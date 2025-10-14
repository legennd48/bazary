import os
from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bazary.settings.development")

app = Celery("bazary")

# Read CELERY_* settings from Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover tasks.py in installed apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):  # pragma: no cover
    print(f"Request: {self.request!r}")
