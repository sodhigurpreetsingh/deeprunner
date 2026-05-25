"""Celery application configuration"""
from celery import Celery
from app.core.config import settings

# Initialize Celery app
celery_app = Celery(
    "docsearch",
    broker=settings.rabbitmq_url,
    backend="rpc://",  # Use RabbitMQ as result backend
    include=["app.worker.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Task routing
celery_app.conf.task_routes = {
    "app.worker.tasks.index_document": {"queue": "document.index", "priority": 9},
    "app.worker.tasks.batch_index_documents": {"queue": "document.batch", "priority": 5},
    "app.worker.tasks.delete_document": {"queue": "document.delete", "priority": 9},
}
