import os
import celery
from celery.utils.log import get_task_logger
from dotenv import load_dotenv

load_dotenv()
logger = get_task_logger(__name__)

app = celery.Celery(
    "streams_project",
    backend=os.environ.get("CELERY_BACKEND"),
    broker=os.environ.get("CELERY_BROKER"),
    include=["worker"]
)

# 并发
app.conf.worker_concurrency = int(os.environ.get("WORKER_CONCURRENCY"))
