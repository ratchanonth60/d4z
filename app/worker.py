from celery import Celery

from app.core.config import settings  # Import your application settings

# Set the default Django settings module for the 'celery' program.
# This might not be strictly necessary if you're not using Django features directly in tasks,
# but it's a common pattern. Adjust if not needed.
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')

# Create Celery application instance
# The first argument is the name of the current module, used for naming tasks.
# The `broker` and `backend` arguments specify the message broker (Redis) and result backend.
celery_app = Celery(
    __name__,  # You can name your main Celery app module 'tasks' or similar
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.email_tasks"
    ],  # List of modules to import when the worker starts
)

# Optional configuration, see the Celery documentation for more details.
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],  # Ignore other content
    result_serializer="json",
    timezone="UTC",  # Or your preferred timezone
    enable_utc=True,
    # broker_connection_retry_on_startup=True # For Celery 5+
    broker_transport_options={
        "max_retries": 10,  # Number of retries
        "interval_start": 0,  # Do not sleep initially
        "interval_step": 0.5,  # Increase delay by 0.5s per retry
        "interval_max": 3,  # Maximum delay between retries is 3s
    },
)


@celery_app.task
def divide(x, y):
    import time

    time.sleep(5)
    return x / y


# If you have tasks in other files, Celery can automatically discover them.
# celery_app.autodiscover_tasks() # This would look for tasks.py in installed apps if using Django structure.
# For FastAPI, explicitly listing in `include` is often clearer.

if __name__ == "__main__":
    # This is for running the worker directly, e.g., `python app/worker.py worker -l info`
    # However, typically you'd run `celery -A app.worker.celery_app worker -l info`
    celery_app.start()
