from airflow import DAG
from operators.bash_script_scenar_1_next_tasks import run_monte_carlo_next_task
from operators.bash_script_scenar_1_first_task import run_monte_carlo_first_task
from datetime import datetime

WORKFLOW_NUMBER = 1

with DAG(
    dag_id="monte_carlo_single_4X1_tasks_1",
    start_date=datetime(2024, 1, 1),
    schedule="*/5 * * * *",
    catchup=False
) as dag:

    task_1 = run_monte_carlo_first_task(
        task_id=f"mc_task_1_wf{WORKFLOW_NUMBER}",
        params = {
        "workflow_number": WORKFLOW_NUMBER,
        "scheduling_interval": 300,
        "task": "task_1",
        }
    )


    task_2 = run_monte_carlo_next_task(
        task_id=f"mc_task_2_wf{WORKFLOW_NUMBER}",
        params = {
        "workflow_number": WORKFLOW_NUMBER,
        "previous_task_id": task_1.task_id,
        "scheduling_interval": 300,
        "task": "task_2",
        }
    )

    task_3 = run_monte_carlo_next_task(
        task_id=f"mc_task_3_wf{WORKFLOW_NUMBER}",
        params = {
        "workflow_number": WORKFLOW_NUMBER,
        "previous_task_id": task_2.task_id,
        "scheduling_interval": 300,
        "task": "task_3",
        }
    )

    task_4 = run_monte_carlo_next_task(
        task_id=f"mc_task_4_wf{WORKFLOW_NUMBER}",
        params = {
        "workflow_number": WORKFLOW_NUMBER,
        "previous_task_id": task_3.task_id,
        "scheduling_interval": 300,
        "task": "task_4",
        }
    )

    task_1 >> task_2 >> task_3 >> task_4