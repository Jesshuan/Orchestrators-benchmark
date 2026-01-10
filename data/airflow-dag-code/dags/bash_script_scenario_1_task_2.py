from airflow import DAG
from operators.bash_script_scenar_1_first_task import run_monte_carlo_first_task
from datetime import datetime

with DAG(
    dag_id="monte_carlo_single_task_wf_2",
    start_date=datetime(2024, 1, 1),
    schedule="*/5 * * * *",
    catchup=False,
    
) as dag:

    run_monte_carlo_first_task(task_id="monte_carlo_single_task_1",
                               params={
        "scheduling_interval": 300,
        "workflow_number": 2,
        "task": 1,
    }).dag = dag