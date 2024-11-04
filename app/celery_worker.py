from celery import Celery
import os

broker_url = os.getenv('BROKER_URL', 'redis://localhost:6379/0')
backend_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

celery = Celery('tasks', broker=broker_url, backend=backend_url)
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)


import app.tasks
