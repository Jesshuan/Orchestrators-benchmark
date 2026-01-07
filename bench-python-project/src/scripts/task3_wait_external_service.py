import os
import requests
import time
import math
import argparse
import json


#### Configuration ####

SCENARIO = "scenario_2_a"
TASK = "task_3"

####  Parameters (env) ####


PUSHGATEWAY = os.environ["PUSHGATEWAY_URL"]

# ---------- EXTERNAL ----------
EXTERNAL_SERVICE_URL = os.environ["EXTERNAL_SERVICE_URL"]
# ----------------------------

#### Observability tools ###

def now():
    return time.time()


def truncate_to_interval(ts, interval_seconds=300):
    """
    Truncate a timestamp to the previous interval boundary.
    interval_seconds = 300 for 5 minutes
    """
    return math.floor(ts / interval_seconds) * interval_seconds



def push_metrics(scheduling_delay, execution_duration, end_to_end, workflow_number: int = 1):
    body = (
        f'benchmark_scheduling_delay_seconds{{scenario="{SCENARIO}"}} {scheduling_delay}\n'
        f'benchmark_execution_duration_seconds{{scenario="{SCENARIO}"}} {execution_duration}\n'
        f'benchmark_end_to_end_latency_seconds{{scenario="{SCENARIO}"}} {end_to_end}\n'
    )

    url = (
        f"{PUSHGATEWAY}/metrics/job/benchmark/workflow_number/{workflow_number}/task/{TASK}"
    )

    print(f'send body payload :\n{body}')
    print(f"to url : {url}")

    requests.post(url, data=body.encode("utf-8"), timeout=3)


### Script ###



def main(workflow_number: int = 1):

    # ---- External blocking wait ----
    print("Calling external service (blocking wait)...")
    r = requests.get(EXTERNAL_SERVICE_URL, timeout=120)
    r.raise_for_status()
    print("External service finished")

if __name__ == "__main__":

    print("Script started : task3_wait_external_service.py")

    parser = argparse.ArgumentParser(
        prog='Task3Script'
    )

    parser.add_argument('-si', '--scheduling_interval', default=300)
    parser.add_argument('-st', '--scheduling_time', default=None)
    parser.add_argument('-wf', '--worflow_number', default=1)

    args = parser.parse_args()
    wf = int(args.worflow_number)
    scheduling_interval = int(args.scheduling_interval)
    scheduling_time = args.scheduling_time

    start_ts = now()
    if scheduling_time:
        scheduled_ts = float(scheduling_time)
    else:
        scheduled_ts = truncate_to_interval(start_ts, interval_seconds=scheduling_interval)

    main(workflow_number=wf)
    
    end_ts = now()

    # Push metrics to Pushgateway

    scheduling_delay = start_ts - scheduled_ts
    execution_duration = end_ts - start_ts
    end_to_end = end_ts - scheduled_ts

    push_metrics(scheduling_delay, execution_duration, end_to_end, workflow_number=wf)

    result = {
        "scenario" : SCENARIO,
        "task" : TASK,
        "workflow_number" : wf,
        "start_ts" : start_ts,
        "scheduled_ts" : scheduled_ts,
        "end_ts" : end_ts,
    }

    print("--- Result ---")
    print(json.dumps(result))