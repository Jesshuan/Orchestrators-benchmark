
import json
import duckdb

from temporalio import activity

from .utils import load_config, now, truncate_to_interval, push_metrics, IOBoundTaskParams, RuntimeConfig

SCENARIO = "scenario_2_b"
TASK = "task_4"


def copy_s3_to_postgres(
    cfg: RuntimeConfig,
    workflow_number: int,
):
    parquet_uri = f"s3://{cfg.output_bucket}/users-aggr-wf-{workflow_number}.parquet"

    con = duckdb.connect(database=":memory:")

    postgres_dsn = (
    f"dbname={cfg.pg_db} "
    f"host={cfg.pg_host} "
    f"port={cfg.pg_port} "
    f"user={cfg.pg_user} "
    f"password={cfg.pg_password}")

    # Enable extensions
    con.execute("INSTALL httpfs;")
    con.execute("LOAD httpfs;")
    con.execute("INSTALL postgres;")
    con.execute("LOAD postgres;")

    # ---- MinIO config ----
    con.execute(f"""
        SET s3_endpoint='{cfg.minio_endpoint.replace("http://", "").replace("https://", "")}';
        SET s3_access_key_id='{cfg.minio_access_key}';
        SET s3_secret_access_key='{cfg.minio_secret_key}';
        SET s3_use_ssl={'false' if cfg.minio_endpoint.startswith("http://") else 'true'};
        SET s3_url_style='path';
    """)


    con.execute(f"""
            ATTACH '{postgres_dsn}'
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


@activity.defn
def task4_s3_copy_to_postgres(
    params: IOBoundTaskParams
):
    cfg = load_config()

    start_ts = now()

    if params.scheduling_time is not None:
        scheduled_ts = float(params.scheduling_time)
    else:
        scheduled_ts = truncate_to_interval(
            start_ts,
            interval_seconds=params.scheduling_interval,
        )

    # ---- Compute ----
    copy_s3_to_postgres(
        cfg=cfg,
        workflow_number=params.workflow_number,
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
        workflow_number=params.workflow_number,
        pushgateway_url=cfg.pushgateway,
        scenario=SCENARIO,
        task=TASK,
    )

    result = {
        "scenario": SCENARIO,
        "task": TASK,
        "workflow_number": params.workflow_number,
        "start_ts": start_ts,
        "scheduled_ts": scheduled_ts,
        "end_ts": end_ts,
    }

    print(json.dumps(result))
    return result
