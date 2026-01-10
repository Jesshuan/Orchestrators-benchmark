from airflow import DAG
from airflow.decorators import task
from python_scripts.python_script_scenar_2_b_task_1 import task_1_s3_and_pg_cleanup
from python_scripts.python_script_scenar_2_b_task_2 import task2_s3_ingestion_and_compute
from python_scripts.python_script_scenar_2_b_task_3 import task3_s3_wait_external_service
from python_scripts.python_script_scenar_2_b_task_4 import task4_s3_copy_to_postgres
from datetime import datetime

WORKFLOW_NUMBER = 2
SCHEDULER_INTERVAL = 300  # seconds


# ---- DAG TASKS ----
@task(multiple_outputs=True)
def task_1_cleanup(
    workflow_number: int,
    scheduling_interval: int,
):
    return task_1_s3_and_pg_cleanup(
        workflow_number=workflow_number,
        scheduling_interval=scheduling_interval,
    )

@task(multiple_outputs=True)
def task2_s3_ingestion(
    workflow_number: int,
    scheduling_interval: int,
    scheduling_time: float | None = None,
):
    return task2_s3_ingestion_and_compute(
        workflow_number=workflow_number,
        scheduling_interval=scheduling_interval,
        scheduling_time=scheduling_time,
    )

@task(multiple_outputs=True)
def task3_wait_external(
    workflow_number: int,
    scheduling_interval: int,
    scheduling_time: float | None = None,
):
    return task3_s3_wait_external_service(
        workflow_number=workflow_number,
        scheduling_interval=scheduling_interval,
        scheduling_time=scheduling_time,
    )

@task(multiple_outputs=True)
def task4_s3_copy_to_pg(
    workflow_number: int,
    scheduling_interval: int,
    scheduling_time: float | None = None,
):
    return task4_s3_copy_to_postgres(
        workflow_number=workflow_number,
        scheduling_interval=scheduling_interval,
        scheduling_time=scheduling_time,
    )

# ------------------------------------


# ---- DAG DEFINITION ----


with DAG(
    dag_id="io_bound_scenario_2_b_4_tasks_2",
    start_date=datetime(2024, 1, 1),
    schedule="*/5 * * * *",
    catchup=False
) as dag:


    result_t1 = task_1_cleanup(
        workflow_number=WORKFLOW_NUMBER,
        scheduling_interval=SCHEDULER_INTERVAL,
    )

    result_t2 = task2_s3_ingestion(
        workflow_number=WORKFLOW_NUMBER,
        scheduling_interval=SCHEDULER_INTERVAL,
        scheduling_time=result_t1['end_ts']
    )

    result_t3 = task3_wait_external(
        workflow_number=WORKFLOW_NUMBER,
        scheduling_interval=SCHEDULER_INTERVAL,
        scheduling_time=result_t2['end_ts']
    )

    result_t4 = task4_s3_copy_to_pg(
        workflow_number=WORKFLOW_NUMBER,
        scheduling_interval=SCHEDULER_INTERVAL,
        scheduling_time=result_t3['end_ts']
    )