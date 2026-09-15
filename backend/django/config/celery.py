import os

from celery import Celery

from common.safe_logging import install_safe_logging


# Celery can initialize its own logging before Django app-ready hooks run. Install
# the redaction boundary here as well so broker/startup and task logs are protected.
install_safe_logging()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
