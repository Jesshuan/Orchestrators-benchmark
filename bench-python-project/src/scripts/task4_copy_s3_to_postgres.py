import os
import time
import requests
import math
import duckdb
import argparse
import json


#### Configuration ####

SCENARIO = "scenario_2_a"
TASK = "task_4"

####  Parameters (env) ####

PUSHGATEWAY = os.environ["PUSHGATEWAY_URL"]

# ---------- MINIO ----------
MINIO_ENDPOINT = os.environ["MINIO_ENDPOINT"] 
MINIO_ACCESS_KEY = os.environ["MINIO_ACCESS_KEY"]
MINIO_SECRET_KEY = os.environ["MINIO_SECRET_KEY"]

OUTPUT_BUCKET = os.environ["OUTPUT_BUCKET"]

# ---------- POSTGRES ----------
PG_HOST = os.environ["PG_HOST"]
PG_PORT = os.environ.get("PG_PORT", "5432")
PG_DB = os.environ["PG_DB"]
PG_USER = os.environ["PG_USER"]
PG_PASSWORD = os.environ["PG_PASSWORD"]

POSTGRES_DSN = (
    f"dbname={PG_DB} "
    f"host={PG_HOST} "
    f"port={PG_PORT} "
    f"user={PG_USER} "
    f"password={PG_PASSWORD}")

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

    parquet_uri = f"s3://{OUTPUT_BUCKET}/users-aggr-wf-{workflow_number}.parquet"

    con = duckdb.connect(database=":memory:")

    # Enable extensions
    con.execute("INSTALL httpfs;")
    con.execute("LOAD httpfs;")
    con.execute("INSTALL postgres;")
    con.execute("LOAD postgres;")

    # ---- MinIO config ----
    con.execute(f"""
        SET s3_endpoint='{MINIO_ENDPOINT.replace("http://", "").replace("https://", "")}';
        SET s3_access_key_id='{MINIO_ACCESS_KEY}';
        SET s3_secret_access_key='{MINIO_SECRET_KEY}';
        SET s3_use_ssl={'false' if MINIO_ENDPOINT.startswith("http://") else 'true'};
        SET s3_url_style='path';
    """)


    con.execute(f"""
            ATTACH '{POSTGRES_DSN}'
            AS pg (TYPE postgres);
        """)

    con.execute(f"""
        CREATE TABLE IF NOT EXISTS pg.user_per_days_workflow{workflow_number} (
            signup_date DATE,
            user_count BIGINT
        );
    """)

    con.execute(f"""
        INSERT INTO pg.user_per_days_workflow{workflow_number}
        SELECT
            signup_date,
            user_count
        FROM parquet_scan('{parquet_uri}');
    """)

    con.close()
    print("Task 4 completed")

if __name__ == "__main__":

    print("Script started : task4_copy_s3_to_postgres.py")

    parser = argparse.ArgumentParser(
        prog='Task4Script'
    )

    parser.add_argument('-si', '--scheduling_interval', default=300)
    parser.add_argument('-st', '--scheduling_time', default=None)
    parser.add_argument('-wf', '--worflow_number', default=1)

    args = parser.parse_args()
    wf = int(args.worflow_number)
    scheduling_interval = int(args.scheduling_interval)
    scheduling_time = args.scheduling_time

    start_ts = now()
    if scheduling_time:
        scheduled_ts = float(scheduling_time)
    else:
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