from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import time

def hello():
    print("Hello from Airflow!")
    time.sleep(20)
    print("Done sleeping!")

with DAG(
    dag_id="minimal_test_dag",
    start_date=datetime(2024, 1, 1),
    schedule="*/3 * * * *",
    catchup=False,
    tags=["test"],
) as dag:

    hello_task = PythonOperator(
        task_id="hello_task",
        python_callable=hello,
    )