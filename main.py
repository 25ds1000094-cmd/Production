import time
import uuid
import json
import logging
from collections import deque

from fastapi import FastAPI, Request
from fastapi.responses import Response
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST


app = FastAPI()

# Track startup time
START_TIME = time.time()

# Prometheus counter
# Exposed automatically as http_requests_total
REQUEST_COUNTER = Counter(
    "http_requests",
    "Total number of HTTP requests"
)

# Store recent logs
LOG_BUFFER = deque(maxlen=1000)


# JSON logger setup
class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps(record.msg)


logger = logging.getLogger("request_logger")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)


# Middleware for metrics + structured logs
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())

    # Count every request
    REQUEST_COUNTER.inc()

    response = await call_next(request)

    log_entry = {
        "level": "INFO",
        "ts": time.time(),
        "path": request.url.path,
        "request_id": request_id
    }

    # Save log entry
    LOG_BUFFER.append(log_entry)

    # Write JSON log
    logger.info(log_entry)

    return response


# Work endpoint
@app.get("/work")
def work(n: int = 1):
    # Simulate K units of work
    for _ in range(n):
        pass

    return {
        "email": "25ds1000094@ds.study.iitm.ac.in",
        "done": n
    }


# Prometheus metrics endpoint
@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# Health check endpoint
@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "uptime_s": float(time.time() - START_TIME)
    }


# Logs endpoint
@app.get("/logs/tail")
def logs_tail(limit: int = 10):
    return list(LOG_BUFFER)[-limit:]
