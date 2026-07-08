import time
import uuid
import logging
import json
from collections import deque
from fastapi import FastAPI, Request
from fastapi.responses import Response
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI()

START_TIME = time.time()

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
)

logs = deque(maxlen=1000)


class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps(record.msg)


logger = logging.getLogger("json_logger")
logger.setLevel(logging.INFO)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())

    response = await call_next(request)

    entry = {
        "level": "INFO",
        "ts": time.time(),
        "path": request.url.path,
        "request_id": request_id,
    }

    logs.append(entry)
    logger.info(entry)

    return response


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    http_requests_total.inc()
    response = await call_next(request)
    return response


@app.get("/work")
def work(n: int = 1):
    for _ in range(n):
        pass

    return {
        "email": "25ds1000094@ds.study.iitm.ac.in",
        "done": n
    }


@app.get("/metrics")
def metrics():
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "uptime_s": float(time.time() - START_TIME)
    }


@app.get("/logs/tail")
def logs_tail(limit: int = 10):
    return list(logs)[-limit:]
