import os
import time
import math
import requests
from dataclasses import dataclass

@dataclass(frozen=True)
class RuntimeConfig:
    pushgateway: str
    external_service_url: str
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    output_bucket: str
    input_bucket: str
    input_key: str
    pg_host: str
    pg_port: str
    pg_db: str
    pg_user: str
    pg_password: str


def load_config() -> RuntimeConfig:
    return RuntimeConfig(
        pushgateway=os.environ["PUSHGATEWAY_URL"],
        external_service_url=os.environ["EXTERNAL_SERVICE_URL"],
        minio_endpoint=os.environ["MINIO_ENDPOINT"],
        minio_access_key=os.environ["MINIO_ACCESS_KEY"],
        minio_secret_key=os.environ["MINIO_SECRET_KEY"],
        output_bucket=os.environ["OUTPUT_BUCKET"],
        input_bucket=os.environ["INPUT_BUCKET"],
        input_key=os.environ["INPUT_KEY"],
        pg_host=os.environ["PG_HOST"],
        pg_port=os.environ.get("PG_PORT", "5432"),
        pg_db=os.environ["PG_DB"],
        pg_user=os.environ["PG_USER"],
        pg_password=os.environ["PG_PASSWORD"],
    )


# ---- OBS ----

def now():
    return time.time()


def truncate_to_interval(ts, interval_seconds=300):
    return math.floor(ts / interval_seconds) * interval_seconds


def push_metrics(scheduling_delay,
                 execution_duration,
                 end_to_end,
                 workflow_number: int,
                 pushgateway_url: str,
                 scenario: str,
                 task: str):
    body = (
        f'benchmark_scheduling_delay_seconds{{scenario="{scenario}"}} {scheduling_delay}\n'
        f'benchmark_execution_duration_seconds{{scenario="{scenario}"}} {execution_duration}\n'
        f'benchmark_end_to_end_latency_seconds{{scenario="{scenario}"}} {end_to_end}\n'
    )

    url = (
        f"{pushgateway_url}/metrics/job/benchmark/"
        f"workflow_number/{workflow_number}/task/{task}"
    )

    requests.post(url, data=body.encode("utf-8"), timeout=3)

