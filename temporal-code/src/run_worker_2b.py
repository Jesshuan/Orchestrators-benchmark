import asyncio
import os

from temporalio.client import Client
from temporalio.worker import Worker

from activities.python_scripts.python_script_scenar_2_b_task_1 import task_1_s3_and_pg_cleanup
from activities.python_scripts.python_script_scenar_2_b_task_2 import task2_s3_ingestion_and_compute
from activities.python_scripts.python_script_scenar_2_b_task_3 import task3_s3_wait_external_service
from activities.python_scripts.python_script_scenar_2_b_task_4 import task4_s3_copy_to_postgres
from workflows.workflow_scenar_2_b import IOBound2bWorkflow
from concurrent.futures import ThreadPoolExecutor

NB_THREADS = 1
ACTIVITIES_CONCURRENCY = 1
WORKFLOWS_CONCURRENCY = 1


TEMPORAL_SERVER_ADDRESS = os.environ.get("TEMPORAL_SERVER_ADDRESS", "localhost:7233")
NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "default")

# ----- task queue configuration -----

pod_name = os.environ.get("POD_NAME", "worker-default")
prefix = os.environ.get("TASK_QUEUE_PREFIX", "default")
index_pod = int(pod_name.split("-")[-1]) + 1 # assuming pod name ends with -<index> starting from 0

task_queue = f"{prefix}-{index_pod}"

# -------------------------------------

async def main() -> None:
    client: Client = await Client.connect(TEMPORAL_SERVER_ADDRESS, namespace=NAMESPACE)
    # Run the worker

    activity_executor = ThreadPoolExecutor(max_workers=NB_THREADS)
    
    worker: Worker = Worker(
        client,
        task_queue=task_queue,
        activities = [task_1_s3_and_pg_cleanup,
                      task2_s3_ingestion_and_compute,
                      task3_s3_wait_external_service,
                      task4_s3_copy_to_postgres],
        workflows = [IOBound2bWorkflow],
        activity_executor=activity_executor,
        max_concurrent_workflow_tasks = WORKFLOWS_CONCURRENCY,
        max_concurrent_activities = ACTIVITIES_CONCURRENCY
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())