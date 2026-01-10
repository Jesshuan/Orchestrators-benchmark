
import json
import requests

from python_scripts.utils import load_config, now, truncate_to_interval, push_metrics, RuntimeConfig

SCENARIO = "scenario_2_b"
TASK = "task_3"


# ---- TASK LOGIC ----
def task3_s3_wait_external_service(
    workflow_number: int = 1,
    scheduling_interval: int = 300,
    scheduling_time: float | None = None,
):
    cfg = load_config()

    start_ts = now()

    if scheduling_time is not None:
        scheduled_ts = float(scheduling_time)
    else:
        scheduled_ts = truncate_to_interval(
            start_ts,
            interval_seconds=scheduling_interval,
        )

    # ---- External blocking wait ----
    print("Calling external service (blocking wait)...")
    r = requests.get(cfg.external_service_url, timeout=120)
    r.raise_for_status()
    print("External service finished")

    end_ts = now()

    # ---- Metrics ----
    scheduling_delay = start_ts - scheduled_ts
    execution_duration = end_ts - start_ts
    end_to_end = end_ts - scheduled_ts

    push_metrics(
        scheduling_delay=scheduling_delay,
        execution_duration=execution_duration,
        end_to_end=end_to_end,
        workflow_number=workflow_number,
        pushgateway_url=cfg.pushgateway,
        scenario=SCENARIO,
        task=TASK,
    )

    result = {
        "scenario": SCENARIO,
        "task": TASK,
        "workflow_number": workflow_number,
        "start_ts": start_ts,
        "scheduled_ts": scheduled_ts,
        "end_ts": end_ts,
    }

    print(json.dumps(result))
    return result
