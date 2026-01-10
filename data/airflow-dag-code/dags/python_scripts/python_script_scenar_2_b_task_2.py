
import json
import duckdb

from python_scripts.utils import load_config, now, truncate_to_interval, push_metrics, RuntimeConfig

SCENARIO = "scenario_2_b"
TASK = "task_2"


def run_duckdb_s3_aggregation(
    cfg: RuntimeConfig,
    workflow_number: int,
):
    con = duckdb.connect(database=":memory:")

    # Enable S3 / HTTP filesystem
    con.execute("INSTALL httpfs;")
    con.execute("LOAD httpfs;")

    # DuckDB S3 (MinIO) configuration
    endpoint = cfg.minio_endpoint.replace("http://", "").replace("https://", "")
    use_ssl = "false" if cfg.minio_endpoint.startswith("http://") else "true"

    con.execute(f"""
        SET s3_endpoint='{endpoint}';
        SET s3_access_key_id='{cfg.minio_access_key}';
        SET s3_secret_access_key='{cfg.minio_secret_key}';
        SET s3_use_ssl={use_ssl};
        SET s3_url_style='path';
    """)

    input_uri = f"s3://{cfg.input_bucket}/{cfg.input_key}"
    output_uri = f"s3://{cfg.output_bucket}/users-aggr-wf-{workflow_number}.parquet"

    print(f"Reading parquet from {input_uri}")
    print(f"Writing result to {output_uri}")

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


def task2_s3_ingestion_and_compute(
    workflow_number: int = 1,
    scheduling_interval: int = 300,
    scheduling_time: float | None = None,
):
    cfg = load_config()

    start_ts = now()

    if scheduling_time is not None:
        scheduled_ts = float(scheduling_time)
    else:
        scheduled_ts = truncate_to_interval(
            start_ts,
            interval_seconds=scheduling_interval,
        )

    # ---- Compute ----
    run_duckdb_s3_aggregation(
        cfg=cfg,
        workflow_number=workflow_number,
    )

    end_ts = now()

    # ---- Metrics ----
    scheduling_delay = start_ts - scheduled_ts
    execution_duration = end_ts - start_ts
    end_to_end = end_ts - scheduled_ts

    push_metrics(
        scheduling_delay=scheduling_delay,
        execution_duration=execution_duration,
        end_to_end=end_to_end,
        workflow_number=workflow_number,
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
