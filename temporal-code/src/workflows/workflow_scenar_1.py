from temporalio import workflow
from activities.bash_activities import run_monte_carlo_task, MonteCarloTaskParams
from datetime import timedelta
from dataclasses import dataclass

@dataclass
class MonteCarloWorkflowDefinition:
    scheduling_interval: int = 300
    workflow_number: int = 1
    nb_tasks: int = 1


@workflow.defn(name="monte_carlo_workflow")
class MonteCarloWorkflow:
    @workflow.run
    async def run(self, wf_def: MonteCarloWorkflowDefinition):
        last_result = None
        for task_nb in range(wf_def.nb_tasks):
            task_name = f"task_{task_nb+1}"
            
            params = MonteCarloTaskParams(
                scheduling_interval=wf_def.scheduling_interval,
                workflow_number=wf_def.workflow_number,
                task_name=task_name,
                last_result=last_result
            )
            
            last_result = await workflow.execute_activity(
                run_monte_carlo_task,
                params,
                start_to_close_timeout=timedelta(seconds=wf_def.scheduling_interval * 10)
            )
        return last_result