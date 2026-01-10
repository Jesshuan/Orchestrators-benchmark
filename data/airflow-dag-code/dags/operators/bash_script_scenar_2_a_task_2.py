from airflow.operators.bash import BashOperator


def run_scenar_2_a_task_2(task_id: str, params: dict):

    return BashOperator(
        task_id=task_id,
        params=params,
        bash_command=r"""
        scheduling_interval="{{ params.scheduling_interval | default(300) }}"
        workflow_number="{{ params.workflow_number | default(1) }}"
        last_result='{{ ti.xcom_pull(task_ids=params.previous_task_id) }}'
        
        echo "last result : $last_result"
        
        if [[ -n "$last_result" ]]; then
          # Write to temp file to avoid escaping issues
          echo "$last_result" > /tmp/xcom_$$.json
          
          # Parse JSON from file
          end_time=$(python3 -c "import json; data=json.load(open('/tmp/xcom_$$.json')); print(data.get('end_ts', ''))")
          
          # Clean up temp file
          rm -f /tmp/xcom_$$.json
          
          if [[ -n "$end_time" ]]; then
            echo "end_time value $end_time retrieved from XCom..."
            python3 /opt/airflow/scripts/task2_s3_ingestion_and_compute.py \
              -st "$end_time" \
              -wf "$workflow_number" \
              | awk '/^{/{json=$0} END{print json}'
          else
            echo "No end_ts found in JSON, using scheduling_interval"
            python3 /opt/airflow/scripts/task2_s3_ingestion_and_compute.py \
              -si "$scheduling_interval" \
              -wf "$workflow_number" \
              | awk '/^{/{json=$0} END{print json}'
          fi
        else
          echo "No last_result found, using scheduling_interval"
          python3 /opt/airflow/scripts/task2_s3_ingestion_and_compute.py \
            -si "$scheduling_interval" \
            -wf "$workflow_number" \
            | awk '/^{/{json=$0} END{print json}'
        fi
        """,
    )