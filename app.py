import celery
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

app = celery.Celery(
    "streams_project",
    backend="redis://127.0.0.1:6379/0",
    broker="redis://127.0.0.1:6379/1",
    include=["worker"]
)

# 3并发
app.conf.worker_concurrency = 3
