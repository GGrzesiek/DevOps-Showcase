import os
from prometheus_client import Counter, Histogram, Gauge

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP request count",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)

APP_INFO = Gauge(
    "app_info",
    "Application metadata",
    ["version", "environment"],
)

APP_INFO.labels(
    version=os.getenv("APP_VERSION", "dev"),
    environment=os.getenv("APP_ENV", "development"),
).set(1)
