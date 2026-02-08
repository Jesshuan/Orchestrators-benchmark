from airflow.operators.bash import BashOperator


def run_scenar_2_a_task_1(task_id: str, params: dict, queue: str = 'default'):

    return BashOperator(
        task_id=task_id,
        params=params,
        queue=queue,
        bash_command=r"""
        scheduling_interval="{{ params.scheduling_interval | default(300) }}"
        workflow_number="{{ params.workflow_number | default(1) }}"
        task="{{ params.task | default('task_1') }}"

        echo "No end_time found, using scheduling_interval"
        python3 /opt/airflow/scripts/task1_delete_s3_and_tables.py \
          -si "$scheduling_interval" \
          -wf "$workflow_number" \
          | awk '/^{/{json=$0} END{print json}'
        """,
    )