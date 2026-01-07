import os
import boto3
import argparse
import sys
import psycopg2
import time
import math
import requests
import json

#### Configuration ####

SCENARIO = "scenario_2_a"
TASK = "task_1"

####  Parameters (env) ####

PUSHGATEWAY = os.environ["PUSHGATEWAY_URL"]

# -------- MINIO CONFIG --------
MINIO_ENDPOINT = os.environ["MINIO_ENDPOINT"] 
MINIO_ACCESS_KEY = os.environ["MINIO_ACCESS_KEY"]
MINIO_SECRET_KEY = os.environ["MINIO_SECRET_KEY"]

OUTPUT_BUCKET = os.environ["OUTPUT_BUCKET"]
# -----------------------------


# ---------- POSTGRES ----------
PG_HOST = os.environ["PG_HOST"]
PG_PORT = os.environ.get("PG_PORT", "5432")
PG_DB = os.environ["PG_DB"]
PG_USER = os.environ["PG_USER"]
PG_PASSWORD = os.environ["PG_PASSWORD"]
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


def main(workflow_number: int = 1):

    print("--- S3 DELETION ---")

    output_key = f"users-aggr-wf-{workflow_number}.parquet"

    s3 = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name="us-east-1",
    )

    try:
        s3.delete_object(Bucket=OUTPUT_BUCKET, Key=output_key)
        print(f"Deleted existing object: s3://{OUTPUT_BUCKET}/{output_key}", file=sys.stderr)
    except Exception as e:
        # Deleting a non-existing object is fine for benchmarks
        print(f"No existing object to delete ({e})", file=sys.stderr)


    print("--- POSTGRES TABLE DELETION ---")

    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
    )
    cur = conn.cursor()

    cur.execute(f"""
        DROP TABLE IF EXISTS user_per_days_workflow{workflow_number}
    """)


    conn.commit()
    cur.close()
    conn.close()


  
if __name__ == "__main__":

    print("Script started : task1_s3_ingestion_and_compute.py")

    parser = argparse.ArgumentParser(
        prog='Task1Script'
    )

    parser.add_argument('-si', '--scheduling_interval', default=300)
    parser.add_argument('-wf', '--worflow_number', default=1)

    args = parser.parse_args()
    wf = int(args.worflow_number)
    scheduling_interval = int(args.scheduling_interval)

    start_ts = now()
    scheduled_ts = truncate_to_interval(start_ts, interval_seconds=scheduling_interval)

    main(workflow_number=wf)
    
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

    print("--- Result ---")
    print(json.dumps(result))


