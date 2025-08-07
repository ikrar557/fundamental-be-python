from .celery import app as celery_app
import logging_config

__all__ = ('celery_app',)