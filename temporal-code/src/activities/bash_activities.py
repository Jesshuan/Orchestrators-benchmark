# activities.py
from temporalio import activity
import subprocess
import json

from dataclasses import dataclass

@dataclass
class MonteCarloTaskParams:
    scheduling_interval: int
    workflow_number: int
    task_name: str
    last_result: dict | None


@dataclass
class IOBoundTaskParams:
    scheduling_interval: int
    workflow_number: int
    last_result: dict | None
    python_script_path: str


@activity.defn
def run_monte_carlo_task(
    params: MonteCarloTaskParams,
) -> dict:
    if params.last_result and "end_ts" in params.last_result:
        print(f"end_time value : {params.last_result["end_ts"]} retrieved from last_result...")
        cmd = [
            "python3", "/app/python-benchmark/src/scripts/monte_carlo.py",
            "-st", str(params.last_result["end_ts"]),
            "-wf", str(params.workflow_number),
            "-t", params.task_name,
        ]
    else:
        cmd = [
            "python3", "/app/python-benchmark/src/scripts/monte_carlo.py",
            "-si", str(params.scheduling_interval),
            "-wf", str(params.workflow_number),
            "-t", params.task_name,
        ]

    print(f"Executing command: {' '.join(cmd)}")
    result = subprocess.check_output(cmd, text=True)

    # extract last JSON line like your awk
    json_line = next(line for line in result.splitlines() if line.startswith("{"))
    print(f"JSON output: {json_line}")

    return json.loads(json_line)


@activity.defn
def run_io_bound_task(
    params: IOBoundTaskParams,
) -> dict:
    if params.last_result and "end_ts" in params.last_result:
        print(f"end_time value : {params.last_result["end_ts"]} retrieved from last_result...")
        cmd = [
            "python3", params.python_script_path,
            "-st", str(params.last_result["end_ts"]),
            "-wf", str(params.workflow_number),
        ]
    else:
        cmd = [
            "python3", params.python_script_path,
            "-si", str(params.scheduling_interval),
            "-wf", str(params.workflow_number),
        ]

    print(f"Executing command: {' '.join(cmd)}")
    result = subprocess.check_output(cmd, text=True)

    # extract last JSON line like your awk
    json_line = next(line for line in result.splitlines() if line.startswith("{"))
    print(f"JSON output: {json_line}")

    return json.loads(json_line)