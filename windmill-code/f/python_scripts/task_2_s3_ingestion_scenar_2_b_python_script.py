import os
import duckdb
import requests
import time
import math


#### Configuration ####

SCENARIO = "scenario_2_b"
TASK = "task_2"

####  Parameters (env) ####

PUSHGATEWAY = os.environ["PUSHGATEWAY_URL"]

# -------- MINIO CONFIG --------
MINIO_ENDPOINT = os.environ["MINIO_ENDPOINT"]  # http://minio.minio.svc.cluster.local:9000
MINIO_ACCESS_KEY = os.environ["MINIO_ACCESS_KEY"]
MINIO_SECRET_KEY = os.environ["MINIO_SECRET_KEY"]

INPUT_BUCKET = os.environ["INPUT_BUCKET"]
INPUT_KEY = os.environ["INPUT_KEY"]

OUTPUT_BUCKET = os.environ["OUTPUT_BUCKET"]
# -----------------------------


#### Observability tools ###

def now():
    return time.time()


def truncate_to_interval(ts, interval_seconds=300):
    """
    Truncate a timestamp to the previous interval boundary.
    interval_seconds = 300 for 5 minutes
    """
    return math.floor(ts / interval_seconds) * interval_seconds



def push_metrics(scheduling_delay, execution_duration, end_to_end, workflow_number: int = 1):
    body = (
        f'benchmark_scheduling_delay_seconds{{scenario="{SCENARIO}"}} {scheduling_delay}\n'
        f'benchmark_execution_duration_seconds{{scenario="{SCENARIO}"}} {execution_duration}\n'
        f'benchmark_end_to_end_latency_seconds{{scenario="{SCENARIO}"}} {end_to_end}\n'
    )

    url = (
        f"{PUSHGATEWAY}/metrics/job/benchmark/workflow_number/{workflow_number}/task/{TASK}"
    )

    print(f'send body payload :\n{body}')
    print(f"to url : {url}")

    requests.post(url, data=body.encode("utf-8"), timeout=3)


### Script ###



def sub_main(workflow_number: int = 1):

    con = duckdb.connect(database=":memory:")

    minio_endpoint = MINIO_ENDPOINT.replace("http://", "").replace("https://", "")

    # Enable S3 / HTTP filesystem
    con.execute("INSTALL httpfs;")
    con.execute("LOAD httpfs;")

    # Configure MinIO (S3-compatible)
    params_s3 = f"""
        SET s3_endpoint='{minio_endpoint}';
        SET s3_access_key_id='{MINIO_ACCESS_KEY}'; SET s3_secret_access_key='{MINIO_SECRET_KEY}';
        SET s3_use_ssl={'false' if MINIO_ENDPOINT.startswith("http://") else 'true'};
        SET s3_url_style='path';
        """
    con.execute(params_s3)

    input_uri = f"s3://{INPUT_BUCKET}/{INPUT_KEY}"
    output_uri = f"s3://{OUTPUT_BUCKET}/users-aggr-wf-{workflow_number}.parquet"

    print(f"Reading parquet directly from {input_uri}")

    con.execute(f"""
        COPY ( 
            SELECT 
                signup_date, 
                COUNT(DISTINCT "user") AS user_count 
            FROM parquet_scan('{input_uri}')
            GROUP BY signup_date 
            ORDER BY signup_date 
        ) 
        TO '{output_uri}' 
        (FORMAT PARQUET); 
    """)

    con.close()
    print("Task 1 completed (direct S3 → S3)")

def main(scheduling_interval: int = 300,
            scheduling_time: float | None = None,
            worflow_number: int = 1):

    print("Script started : task1_s3_ingestion_and_compute.py")

    wf = int(worflow_number)

    start_ts = now()

    if scheduling_time:
        scheduled_ts = float(scheduling_time)
    else:
        scheduled_ts = truncate_to_interval(start_ts, interval_seconds=scheduling_interval)

    sub_main(workflow_number=wf)
    
    end_ts = now()

    # Push metrics to Pushgateway

    scheduling_delay = start_ts - scheduled_ts
    execution_duration = end_ts - start_ts
    end_to_end = end_ts - scheduled_ts

    push_metrics(scheduling_delay, execution_duration, end_to_end, workflow_number=wf)

    result = {
        "scenario" : SCENARIO,
        "task" : TASK,
        "workflow_number" : wf,
        "start_ts" : start_ts,
        "scheduled_ts" : scheduled_ts,
        "end_ts" : end_ts,
    }

    return result