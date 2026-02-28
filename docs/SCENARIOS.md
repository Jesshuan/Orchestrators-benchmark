# Benchmark Scenarios

Detailed explanation of each benchmark scenario and the workloads they test.

---

## Table of Contents

1. [Overview](#overview)
2. [Scenario 1: CPU-Intensive (Monte Carlo)](#scenario-1-cpu-intensive-monte-carlo)
3. [Scenario 2: I/O-Bound (2A & 2B)](#scenario-2-io-bound)
   - [Variant 2A: Bash Subprocess](#variant-a)
   - [Variant 2B: Pure Python](#variant-b)
4. [Metrics Collection](#metrics-collection)
5. [Running Scenarios](#running-scenarios)

---

## Overview

The benchmark suite includes three scenarios designed to test different aspects of orchestrator performance:

| Scenario | Type | Workflow Tasks | Purpose |
|----------|------|-------|---------|
| **1** | CPU-Intensive | 1 or 4 | Tests pure computational workload and scheduling overhead |
| **2A** | I/O-Bound | 4 sequential | Tests realistic data pipeline with subprocess overhead |
| **2B** | I/O-Bound | 4 sequential | Tests realistic data pipeline with pure Python (no subprocess) |

Each scenario runs on a **5-minute schedule** (`*/5 * * * *`) and collects comprehensive metrics.

Each workflow, based on a scenario, can be launched with a concurrency of 1, 4 or 12. This produces multiple variants for one scenario.

### Near to a fair equity about execution mode

It is not very straightforward to build a fair benchmark between all the orchestrators...
Orchestrators use different paradigms, not very equivalent.
For example, about the execution mode subject, Windmill and Temporal primarily use the 'permanent' workers paradigm. A task is sent to a worker already up, to prevent cold start problems... We can use Keda and auto-scaling, but it's rarely a good deal for these orchestrators : workers don't consume many resources when they are inactive, and a lot of usage probably justifies using worker groups that are permanently running, despite of the fact that these workers request permanently a few cpu and memory.
In contrast, Argo Workflow, and the use of the Cron Workflows as scheduled workflows, is definitively linked to the 'ephemeral' pod paradigm, where workflows are only running during the task treatment. The simplicity of this 'Kubernetes' native orchestrator results in good latency too, despite the fact that there will be an irreducible latency for the Kubernetes pod startup, for each task to run.
Airflow can be used with 'KubernetesExecutor' mode (like Argo Workflows paradigm) or 'CeleryExecutor' like Windmill and Temporal.

What we've decided here ?

#### scenario 1, 2a, 2b : 'Celery-like' execution mode

Scenario 1, 2a & 2b are built around the 'Celery-like' execution mode : workers are permanent, except for Argo Workflow that can't.
Argo Workflow (present on scenario 1 and 2a, not 2b) could not be evaluated on latency (scheduling time), but it still allows comparing it with other orchestrators on the resources used (cpu / memory) and execution time.


#### scenario 1c, 2c (future): 'Kubernetes-like' execution mode ?

In a near future, a scenario 1c and 2c should be interesting, for a 'Kubernetes-like' execution mode : all the orchestrators should be evaluated with ephemeral workers paradigm, and bash scripts wrapper, to totally include Argo Workflow.
But on a local kind cluster, we've met some difficulties to organize this : Airflow need more resource and more stability for the 'KubernetesExecutor' mode. 


---

## Scenario 1: CPU-Intensive (Monte Carlo)

### Purpose

Test orchestrator performance with **pure computational workloads** that are CPU-bound with minimal I/O.

### Workload Description

Calculates the value of Pi using the Monte Carlo method with **20 million iterations**. This is a computationally expensive operation that stresses the CPU.

**Algorithm:**
```python
def monte_carlo_pi(num_samples):
    inside_circle = 0
    for _ in range(num_samples):
        x, y = random.random(), random.random()
        if x*x + y*y <= 1:
            inside_circle += 1
    return 4 * inside_circle / num_samples
```

### Workflow variants

#### Execution mode

To fully include Argo Workflow in this cpu-intensive scenario, and measure the resources used, we've decided to launch the python scripts with bash scripts (bash wrapper script), for a fair comparison with the Argo Workflow orchestrator which has no native Python task definition.

#### workflow type 1 : 1 workflow = 1 single Task
- **1 task** per workflow execution
- Tests basic scheduling and execution overhead

#### workflow type 2: 1 workflow = 4 Sequential Tasks
- **4 identical tasks** executed sequentially
- Tests task chaining and inter-task communication overhead

These two workflow type variants are also tested according to a different concurrency setup, at the workflow level:
- 1 unique workflow launched every 5 minutes
- 4 workflows launched in parallel every 5 minutes
- 12 workflows launched in parallel every 5 minutes BUT concurrency forced to 4. Indeed, this is a "stress" test for the orchestrator, cause we have a lot of pending workflow at the same time, to solve during a 5 minute window.

The combination of these setups produces all these effective variants :
- 1X1, for "1 workflow of 1 task" / bash script => python script
- 4X1, for "4 workflows of 1 task" in parallel / bash script => python script
- 1X4, for "1 workflow of 4 sequential tasks" / bash script => python script
- 4X4, for "4 workflows of 4 sequential tasks" in parallel / bash script => python script

### Schedule

Each workflow runs every **5 minutes** (`*/5 * * * *`) during a 'stable' observability period : 30 minutes. 




### Code Location

- **Core script**: `bench-python-project/src/scripts/monte_carlo.py`
- **Airflow DAG**: `data/airflow-dag-code/dags/bash_script_scenario_1_a_*.py`
- **Windmill flow**: `windmill-code/f/flows_scenar_1/`
- **Argo Workflow**: `argo-wf-values/cron-workflow-generation/scenar_1/cron_wf_scenar_1_mc_*.yaml`
- **Temporal workflow**: `temporal-code/src/workflows/workflow_scenar_1_a.py`

---

## Scenario 2: I/O-Bound

### Purpose

Test orchestrator performance with **realistic I/O-bound data pipelines** that interact with external services (S3, PostgreSQL, APIs).



### Workload Description

A 4-task sequential data pipeline:

```
Task 1: Clean up → Task 2: Ingest & Process → Task 3: Wait for Service → Task 4: Load Data
```

#### Task 1: Delete S3 & Drop Tables
- Deletes objects from MinIO S3 (`output-data` bucket)
- Drops PostgreSQL table (`elt.users`)
- **Purpose**: Clean slate for the pipeline

#### Task 2: S3 Ingestion & Compute
- Reads `users.parquet` from S3 (`input-data` bucket)
- Processes data with DuckDB (SQL transformations)
- Writes processed data to S3 (`output-data` bucket)
- **Purpose**: Test S3 I/O and data processing

#### Task 3: Wait for External Service
- Calls external FastAPI service endpoint: `/sleep/30`
- Waits for 30 seconds (simulates external system dependency)
- **Purpose**: Test external service integration and waiting behavior

#### Task 4: Copy S3 to PostgreSQL
- Reads processed data from S3
- Loads data into PostgreSQL table (`elt.users`)
- **Purpose**: Test database I/O and bulk inserts

### Execution Pattern

- **Sequential execution**: Each task waits for the previous task to complete
- **Multiple instances**: Runs 1-12 parallel instances to test concurrency

### Two variants : A and B

#### variant A

This variant uses **bash scripts** that launch Python subprocess, mimicking real-world patterns where workflows shell out to external scripts.
Why bash script ?
Because Argo Workflow needs to be present in this benchmark variant. And it is fair to wrap all the python scripts with bash scripts for all the orchestrators.
(but this is not entirely fair for latency metrics for Argo Workflow as mentioned...)

#### variant B

This variant uses **python scripts** in the paradigm of each orchestrator : PythonOperator for Airflow with task decorator, SDK built python tasks with Temporal, 'direct' python scripts with Windmill...
Now, we can use the orchestrator as it would be used in the real world.
ArgoWorkflow is absent for this variant.

#### Differences between 2A & 2B scenarios

| Aspect | Scenario 2A | Scenario 2B |
|--------|-------------|-------------|
| **Execution** | Bash → Python subprocess | Pure Python |
| **Overhead** | Subprocess creation overhead | No subprocess overhead |
| **Use case** | Real-world scripts | Native language activities |

These two variants are also tested according to a different concurrency setup, at the workflow level:
- 1 unique workflow launched every 5 minutes
- 4 workflows launched in parallel every 5 minutes
- 12 workflows launched in parallel every 5 minutes BUT concurrency forced to 4. Indeed, this is a "stress" test for the orchestrator, cause we have a lot of pending workflow at the same time, to solve during a 5 minute window.

The combination of these setups produces all these effective variants :
- scenar2a_1X4, for "1 workflow of 4 sequential tasks" / bash script => python script
- scenar2a_4X4, for "4 workflows of 4 sequential tasks" in parallel / bash script
- scenar2a_12X4, for "12 workflows of 4 sequential tasks" in parallel, with a concurrency forced to 4 / bash script => python script
- scenar2b_1X4, for "1 workflow of 4 sequential tasks" / python script 
- scenar2b_4X4, for "4 workflows of 4 sequential tasks" in parallel / python script
- scenar2b_12X4, for "12 workflows of 4 sequential tasks" in parallel, with a concurrency forced to 4 / python script

### Schedule

Runs every **5 minutes** (`*/5 * * * *`) with configurable parallelism

### Code Location scenario 2 A

- **Core scripts**: `bench-python-project/src/scripts/task*.py`
- **Bash wrappers**: `windmill-code/f/bash_scripts/` and embedded in orchestrator-specific configurations
- **Airflow DAG**: `data/airflow-dag-code/dags/bash_script_scenario_2_a_4_t_*.py`
- **Windmill flow**: `windmill-code/f/flow_scenar_2/io_bound_flow_scenar_2a_bash-4_tasks.flow/`
- **Argo Workflow**: `argo-wf-values/cron-workflow-generation/scenar_2/cron_wf_scenar_2_a_io_bound_4_tasks_*.yaml`
- **Temporal workflow**: `temporal-code/src/workflows/workflow_scenar_2_a.py`

### Code Location scenario 2 B

- **Core scripts (Windmill)**: `windmill-code/f/python_scripts/task_*_scenar_2_b_python_script.py`
- **Core scripts (Airflow)**: `data/airflow-dag-code/dags/python_script_scenario_2_b_4_task_*.py`
- **Temporal activities**: `temporal-code/src/activities/python_scripts/`
- **Windmill flow**: `windmill-code/f/flow_scenar_2/io_bound_flow_scenar_2b_python-4_tasks.flow/`
- **Temporal workflow**: `temporal-code/src/workflows/workflow_scenar_2_b.py`

---

## Metrics Collection

All scenarios collect standardized metrics using the Prometheus PushGateway.

### Metrics Collected

#### Effective times for achieving the tasks
- Scheduling delay (time from scheduled start to actual start) - mean and max
- Execution duration (time to complete the Monte Carlo calculation) - mean and max
- End-to-end latency (total time from schedule to completion) - mean

#### Resources used
- CPU usage during execution (max and mean) :
permanent pods (server, web UI, etc) / workers / kube system absorption
- Memory usage during execution (max and mean)
permanent pods (server, web UI, etc) / workers / kube system absorption

The resources mean metrics are aggregated over all the 'stable' observability period (30 min), with interruption periods included inside it.
For example, when a worker is not up or has no work, the 0 cpu used value is included inside the final mean.
Indeed :
- if two orchestrators use the same resources to achieve the tasks, but one is faster than the other, the mean cpu of the first observed cpu mean will be higher.
- if two orchestrators achieve the same tasks with the same effective times, but one consumes more cpu than the other, the first observed cpu mean will be higher.

### Metric Types

#### 1. Scheduling Delay
```
benchmark_scheduling_delay_seconds
```
Time from scheduled execution time to actual start time.

**Formula:** `actual_start_time - scheduled_time`

#### 2. Execution Duration
```
benchmark_execution_duration_seconds
```
Time taken to execute the task logic.

**Formula:** `task_end_time - task_start_time`

#### 3. End-to-End Latency
```
benchmark_end_to_end_latency_seconds
```
Total time from schedule to completion.

**Formula:** `completion_time - scheduled_time`

### Metric Labels

All metrics include labels for filtering and aggregation:

```python
labels = {
    "scenario": "scenar_1" | "scenar_2_a" | "scenar_2_b",
    "workflow_number": "1" | "2" | ... | "12",
    "task": "task_1" | "task_2" | "task_3" | "task_4",
    "orchestrator": "airflow" | "argo" | "windmill" | "temporal"
}
```

### Metric Push Implementation

Each task follows this pattern:

```python
import time
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

# Start timing
scheduled_time = get_scheduled_time()
start_time = time.time()

# Execute task
run_task_logic()

# Calculate metrics
end_time = time.time()
scheduling_delay = start_time - scheduled_time
execution_duration = end_time - start_time
end_to_end_latency = end_time - scheduled_time

# Push to Prometheus
registry = CollectorRegistry()
Gauge('benchmark_scheduling_delay_seconds', 'Scheduling delay',
      registry=registry, labelnames=['scenario', 'workflow_number', 'task'])\
    .labels(scenario='scenar_1', workflow_number='1', task='task_1')\
    .set(scheduling_delay)

push_to_gateway('prometheus-pushgateway:9091', job='benchmark', registry=registry)
```

---

## Running Scenarios

### Activate/Deactivate Scenarios

Each orchestrator has its own method for activating schedules:

#### Airflow
- Access WebUI: `http://localhost:8080`
- Toggle DAG on/off using the switch
- View execution history in the DAG runs tab

#### Argo Workflows
- Use CLI to suspend/resume CronWorkflows:
  ```bash
  argo cron suspend <cron-workflow-name> -n team-a
  argo cron resume <cron-workflow-name> -n team-a
  ```
- Or use the Argo UI to suspend/resume schedules

#### Windmill
- Access WebUI: `http://localhost:8000`
- Navigate to **Schedules**
- Enable/disable schedules using the toggle

#### Temporal
- Access WebUI: `http://localhost:8088`
- Navigate to **Schedules**
- Pause/unpause schedules using the action menu

---

## Scenario Comparison Matrix

| Aspect | Scenario 1 | Scenario 2A | Scenario 2B |
|--------|-----------|------------|-------------|
| **Workload type** | CPU-intensive | I/O-bound | I/O-bound |
| **External dependencies** | None | S3, PostgreSQL, FastAPI | S3, PostgreSQL, FastAPI |
| **Subprocess overhead** | Yes (bash → Python) | Yes (bash → Python) | No (pure Python) |
| **Task count** | 1 or 4 | 4 sequential | 4 sequential |
| **Workflow Parallelism** | 1-4 | 1-12 instances | 1-12 instances |

---

## Next Steps

**[Observability Setup](OBSERVABILITY.md)** - Configure monitoring to view scenario metrics

**[Results Analysis](RESULTS.md)** - Analyze benchmark results after running scenarios

---

## Tips for Running Benchmarks

1. **Start with low parallelism**: Begin with 1-2 instances to verify everything works
2. **Monitor resources**: Use k9s or kubectl to watch pod resource usage
3. **Check logs**: Verify tasks are pushing metrics to PushGateway
4. **View in Grafana**: Confirm metrics appear in Grafana dashboards
5. **Increase load gradually**: Scale up to 4, 8, 12 parallel instances
6. **Run for sufficient duration**: Allow at least 30-60 minutes for meaningful data
7. **Clean between runs**: Clear old metrics from PushGateway if needed
8. **Clean between setup**: Clear the previous orchestrator installation before a new one
