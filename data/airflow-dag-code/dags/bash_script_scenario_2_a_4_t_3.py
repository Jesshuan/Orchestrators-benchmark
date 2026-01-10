from airflow import DAG
from operators.bash_script_scenar_2_a_task_1 import run_scenar_2_a_task_1
from operators.bash_script_scenar_2_a_task_2 import run_scenar_2_a_task_2
from operators.bash_script_scenar_2_a_task_3 import run_scenar_2_a_task_3
from operators.bash_script_scenar_2_a_task_4 import run_scenar_2_a_task_4
from datetime import datetime

WORKFLOW_NUMBER = 3

with DAG(
    dag_id="io_bound_scenario_2_a_4_tasks_3",
    start_date=datetime(2024, 1, 1),
    schedule="*/5 * * * *",
    catchup=False
) as dag:

    task_1 = run_scenar_2_a_task_1(
        task_id=f"io_task_1_wf{WORKFLOW_NUMBER}",
        params = {
        "workflow_number": WORKFLOW_NUMBER,
        "scheduling_interval": 300,
        "task": "task_1",
        }
    )


    task_2 = run_scenar_2_a_task_2(
        task_id=f"io_task_2_wf{WORKFLOW_NUMBER}",
        params = {
        "workflow_number": WORKFLOW_NUMBER,
        "previous_task_id": task_1.task_id,
        "scheduling_interval": 300,
        "task": "task_2",
        }
    )

    task_3 = run_scenar_2_a_task_3(
        task_id=f"io_task_3_wf{WORKFLOW_NUMBER}",
        params = {
        "workflow_number": WORKFLOW_NUMBER,
        "previous_task_id": task_2.task_id,
        "scheduling_interval": 300,
        "task": "task_3",
        }
    )

    task_4 = run_scenar_2_a_task_4(
        task_id=f"io_task_4_wf{WORKFLOW_NUMBER}",
        params = {
        "workflow_number": WORKFLOW_NUMBER,
        "previous_task_id": task_3.task_id,
        "scheduling_interval": 300,
        "task": "task_4",
        }
    )

    task_1 >> task_2 >> task_3 >> task_4