import boto3
import psycopg2
import json
import sys

from python_scripts.utils import load_config, now, truncate_to_interval, push_metrics

SCENARIO = "scenario_2_b"
TASK = "task_1"


# ---- TASK LOGIC ----

def task_1_s3_and_pg_cleanup(
    workflow_number: int = 1,
    scheduling_interval: int = 300,
):
    # Load runtime config
    cfg = load_config()

    start_ts = now()
    scheduled_ts = truncate_to_interval(start_ts, scheduling_interval)

    # -------- S3 --------
    output_key = f"users-aggr-wf-{workflow_number}.parquet"

    s3 = boto3.client(
        "s3",
        endpoint_url=cfg.minio_endpoint,
        aws_access_key_id=cfg.minio_access_key,
        aws_secret_access_key=cfg.minio_secret_key,
        region_name="us-east-1",
    )

    try:
        s3.delete_object(Bucket=cfg.output_bucket, Key=output_key)
        print(f"Deleted s3://{cfg.output_bucket}/{output_key}", file=sys.stderr)
    except Exception as e:
        print(f"No object to delete: {e}", file=sys.stderr)

    # -------- POSTGRES --------
    conn = psycopg2.connect(
        host=cfg.pg_host,
        port=cfg.pg_port,
        dbname=cfg.pg_db,
        user=cfg.pg_user,
        password=cfg.pg_password,
    )
    cur = conn.cursor()
    cur.execute(
        f"DROP TABLE IF EXISTS user_per_days_workflow{workflow_number}"
    )
    conn.commit()
    cur.close()
    conn.close()

    end_ts = now()

    scheduling_delay = start_ts - scheduled_ts
    execution_duration = end_ts - start_ts
    end_to_end = end_ts - scheduled_ts

    push_metrics(
        scheduling_delay,
        execution_duration,
        end_to_end,
        workflow_number,
        pushgateway_url=cfg.pushgateway,
        scenario=SCENARIO,
        task=TASK,
    )

    result = {
        "scenario": SCENARIO,
        "task": TASK,
        "workflow_number": workflow_number,
        "start_ts": start_ts,
        "scheduled_ts": scheduled_ts,
        "end_ts": end_ts,
    }

    print(json.dumps(result))
    
    return result

