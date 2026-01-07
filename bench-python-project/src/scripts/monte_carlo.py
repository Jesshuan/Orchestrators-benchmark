import random
import time
import argparse
import os
import requests
import math
import json

#### Configuration ####

SCENARIO = "scenario_1"
DEFAULT_TASK_NUMBER = "task_1"

####  Parameters (env) ####

PUSHGATEWAY = os.environ["PUSHGATEWAY_URL"]



#### Observability tools ###

def now():
    return time.time()


def truncate_to_interval(ts, interval_seconds=300):
    """
    Truncate a timestamp to the previous interval boundary.
    interval_seconds = 300 for 5 minutes
    """
    return math.floor(ts / interval_seconds) * interval_seconds



def push_metrics(scheduling_delay, execution_duration, end_to_end, workflow_number: int = 1, task: str = DEFAULT_TASK_NUMBER):
    body = (
        f'benchmark_scheduling_delay_seconds{{scenario="{SCENARIO}"}} {scheduling_delay}\n'
        f'benchmark_execution_duration_seconds{{scenario="{SCENARIO}"}} {execution_duration}\n'
        f'benchmark_end_to_end_latency_seconds{{scenario="{SCENARIO}"}} {end_to_end}\n'
    )

    url = (
        f"{PUSHGATEWAY}/metrics/job/benchmark/workflow_number/{workflow_number}/task/{task}"
    )

    print(f'send body payload :\n{body}')
    print(f"to url : {url}")

    requests.post(url, data=body.encode("utf-8"), timeout=3)


### Script ###



def monte_carlo_pi(n: int) -> float:
    inside = 0
    for _ in range(n):
        x = random.random()
        y = random.random()
        if x*x + y*y <= 1.0:
            inside += 1
    return 4.0 * inside / n



if __name__ == "__main__":

    print("Script started : monte_carlo.py")

    parser = argparse.ArgumentParser(
        prog='MyMonteCarloScript'
    )

    parser.add_argument('-n', '--number_of_iteration', default=20000000)
    parser.add_argument('-si', '--scheduling_interval', default=300)
    parser.add_argument('-st', '--scheduling_time', default=None)
    parser.add_argument('-wf', '--worflow_number', default=1)
    parser.add_argument('-t', '--task', default=DEFAULT_TASK_NUMBER)

    args = parser.parse_args()


    n = int(args.number_of_iteration)
    wf = int(args.worflow_number)
    scheduling_interval = int(args.scheduling_interval)
    scheduling_time = args.scheduling_time
    task = args.task

    start_ts = now()

    if task != DEFAULT_TASK_NUMBER and scheduling_time is not None:
        scheduled_ts = float(scheduling_time)
    else:
        scheduled_ts = truncate_to_interval(start_ts, interval_seconds=scheduling_interval)
        

    start = time.perf_counter()

    pi = monte_carlo_pi(n)

    end_ts = now()

    duration = time.perf_counter() - start
    print(f"pi={pi}, time={duration:.2f}s")

    # Push metrics to Pushgateway

    scheduling_delay = start_ts - scheduled_ts
    execution_duration = end_ts - start_ts
    end_to_end = end_ts - scheduled_ts

    push_metrics(scheduling_delay, execution_duration, end_to_end, workflow_number=wf, task=task)

    result = {
        "scenario" : SCENARIO,
        "task" : task,
        "workflow_number" : wf,
        "start_ts" : start_ts,
        "scheduled_ts" : scheduled_ts,
        "end_ts" : end_ts,
    }

    print("--- Result ---")
    print(json.dumps(result))



