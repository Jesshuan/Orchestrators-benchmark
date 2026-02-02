import asyncio
import os

from temporalio.client import Client
from temporalio.worker import Worker

from activities.bash_activities import run_monte_carlo_task, run_io_bound_task
from workflows.workflow_scenar_1_a import MonteCarloWorkflow
from workflows.workflow_scenar_2_a import IOBound2aWorkflow
from concurrent.futures import ThreadPoolExecutor

NB_THREADS = 1
ACTIVITIES_CONCURRENCY = 1
WORKFLOWS_CONCURRENCY = 1


TEMPORAL_SERVER_ADDRESS = os.environ.get("TEMPORAL_SERVER_ADDRESS", "localhost:7233")
NAMESPACE = os.environ.get("TEMPORAL_NAMESPACE", "default")

# ----- task queue configuration -----

#pod_name = os.environ.get("POD_NAME", "worker-default")
task_queue = os.environ.get("TASK_QUEUE_PREFIX", "default")
#index_pod = int(pod_name.split("-")[-1]) + 1 # assuming pod name ends with -<index> starting from 0

# -------------------------------------

async def main() -> None:
    client: Client = await Client.connect(TEMPORAL_SERVER_ADDRESS, namespace=NAMESPACE)
    # Run the worker

    activity_executor = ThreadPoolExecutor(max_workers=NB_THREADS)
    
    worker: Worker = Worker(
        client,
        task_queue=task_queue,
        activities = [run_monte_carlo_task, run_io_bound_task],
        workflows = [MonteCarloWorkflow, IOBound2aWorkflow],
        activity_executor=activity_executor,
        max_concurrent_workflow_tasks = WORKFLOWS_CONCURRENCY,
        max_concurrent_activities = ACTIVITIES_CONCURRENCY
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())