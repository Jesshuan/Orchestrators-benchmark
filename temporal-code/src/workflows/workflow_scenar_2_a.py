from temporalio import workflow
from activities.bash_activities import run_io_bound_task, IOBoundTaskParams
from datetime import timedelta
from dataclasses import dataclass

@dataclass
class IOBound2aWorkflowDefinition:
    scheduling_interval: int = 300
    workflow_number: int = 1

@workflow.defn(name="io_bound_2_a_workflow")
class IOBound2aWorkflow:
    @workflow.run
    async def run(self, wf_def: IOBound2aWorkflowDefinition):
        result = None
   
        # -- TASK 1 --
        params_task_1 = IOBoundTaskParams(
            scheduling_interval=wf_def.scheduling_interval,
            workflow_number=wf_def.workflow_number,
            last_result=result,
            python_script_path="/app/python-benchmark/src/scripts/task1_delete_s3_and_tables.py"
        )
        
        result = await workflow.execute_activity(
            run_io_bound_task,
            params_task_1,
            start_to_close_timeout=timedelta(seconds=wf_def.scheduling_interval * 10)
        )

        # -- TASK 2 --
        params_task_2 = IOBoundTaskParams(
            scheduling_interval=wf_def.scheduling_interval,
            workflow_number=wf_def.workflow_number,
            last_result=result,
            python_script_path="/app/python-benchmark/src/scripts/task2_s3_ingestion_and_compute.py"
        )
        
        result = await workflow.execute_activity(
            run_io_bound_task,
            params_task_2,
            start_to_close_timeout=timedelta(seconds=wf_def.scheduling_interval * 10)
        )

        # -- TASK 3 --
        params_task_3 = IOBoundTaskParams(
            scheduling_interval=wf_def.scheduling_interval,
            workflow_number=wf_def.workflow_number,
            last_result=result,
            python_script_path="/app/python-benchmark/src/scripts/task3_wait_external_service.py"
        )
        
        result = await workflow.execute_activity(
            run_io_bound_task,
            params_task_3,
            start_to_close_timeout=timedelta(seconds=wf_def.scheduling_interval * 10)
        )

        # -- TASK 4 --
        params_task_4 = IOBoundTaskParams(
            scheduling_interval=wf_def.scheduling_interval,
            workflow_number=wf_def.workflow_number,
            last_result=result,
            python_script_path="/app/python-benchmark/src/scripts/task4_copy_s3_to_postgres.py"
        )
        
        result = await workflow.execute_activity(
            run_io_bound_task,
            params_task_4,
            start_to_close_timeout=timedelta(seconds=wf_def.scheduling_interval * 10)
        )

        return result