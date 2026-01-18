from temporalio import workflow
from temporalio.common import RetryPolicy
#from activities.python_scripts.utils import IOBoundTaskParams
# from activities.python_scripts.python_script_scenar_2_b_task_1 import task_1_s3_and_pg_cleanup
# from activities.python_scripts.python_script_scenar_2_b_task_2 import task2_s3_ingestion_and_compute
# from activities.python_scripts.python_script_scenar_2_b_task_3 import task3_s3_wait_external_service
# from activities.python_scripts.python_script_scenar_2_b_task_4 import task4_s3_copy_to_postgres
from datetime import timedelta
from dataclasses import dataclass

@dataclass
class IOBoundTaskParams:
    scheduling_interval: int
    workflow_number: int
    scheduling_time: float | None = None

@dataclass
class IOBound2bWorkflowDefinition:
    scheduling_interval: int = 300
    workflow_number: int = 1

@workflow.defn(name="io_bound_2_b_workflow")
class IOBound2bWorkflow:
    @workflow.run
    async def run(self, wf_def: IOBound2bWorkflowDefinition):
        result = None
   
        # -- TASK 1 --
        params_task_1 = IOBoundTaskParams(
            scheduling_interval=wf_def.scheduling_interval,
            workflow_number=wf_def.workflow_number,
            scheduling_time=None
        )
        
        result = await workflow.execute_activity(
            "task_1_s3_and_pg_cleanup",
            params_task_1,
            start_to_close_timeout=timedelta(seconds=wf_def.scheduling_interval * 10),
            retry_policy=RetryPolicy(maximum_attempts=1)
        )

        # -- TASK 2 --
        params_task_2 = IOBoundTaskParams(
            scheduling_interval=wf_def.scheduling_interval,
            workflow_number=wf_def.workflow_number,
            scheduling_time=result['end_ts']
        )
        
        result = await workflow.execute_activity(
            "task2_s3_ingestion_and_compute",
            params_task_2,
            start_to_close_timeout=timedelta(seconds=wf_def.scheduling_interval * 10),
            retry_policy=RetryPolicy(maximum_attempts=1)
        )

        # -- TASK 3 --
        params_task_3 = IOBoundTaskParams(
            scheduling_interval=wf_def.scheduling_interval,
            workflow_number=wf_def.workflow_number,
            scheduling_time=result['end_ts']
        )
        
        result = await workflow.execute_activity(
            "task3_s3_wait_external_service",
            params_task_3,
            start_to_close_timeout=timedelta(seconds=wf_def.scheduling_interval * 10),
            retry_policy=RetryPolicy(maximum_attempts=1)
        )

        # -- TASK 4 --
        params_task_4 = IOBoundTaskParams(
            scheduling_interval=wf_def.scheduling_interval,
            workflow_number=wf_def.workflow_number,
            scheduling_time=result['end_ts']
        )
        
        result = await workflow.execute_activity(
            "task4_s3_copy_to_postgres",
            params_task_4,
            start_to_close_timeout=timedelta(seconds=wf_def.scheduling_interval * 10),
            retry_policy=RetryPolicy(maximum_attempts=1)
        )

        return result