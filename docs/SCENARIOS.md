# Benchmark Scenarios

Detailed explanation of each benchmark scenario and the workloads they test.

---

## Table of Contents

1. [Overview](#overview)
2. [Scenario 1: CPU-Intensive (Monte Carlo)](#scenario-1-cpu-intensive-monte-carlo)
3. [Scenario 2A: I/O-Bound (Bash Subprocess)](#scenario-2a-io-bound-bash-subprocess)
4. [Scenario 2B: I/O-Bound (Pure Python)](#scenario-2b-io-bound-pure-python)
5. [Metrics Collection](#metrics-collection)
6. [Running Scenarios](#running-scenarios)

---

## Overview

The benchmark suite includes three scenarios designed to test different aspects of orchestrator performance:

| Scenario | Type | Tasks | Purpose |
|----------|------|-------|---------|
| **1** | CPU-Intensive | 1 or 4 | Tests pure computational workload and scheduling overhead |
| **2A** | I/O-Bound | 4 sequential | Tests realistic data pipeline with subprocess overhead |
| **2B** | I/O-Bound | 4 sequential | Tests realistic data pipeline with pure Python (no subprocess) |

Each scenario runs on a **5-minute schedule** (`*/5 * * * *`) and collects comprehensive metrics.

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

### Variants

#### Variant 1: Single Task
- **1 task** per workflow execution
- Tests basic scheduling and execution overhead

#### Variant 2: Four Sequential Tasks
- **4 identical tasks** executed sequentially
- Tests task chaining and inter-task communication overhead

### Schedule

Runs every **5 minutes** (`*/5 * * * *`)

### Metrics Collected

- Scheduling delay (time from scheduled start to actual start)
- Execution duration (time to complete the Monte Carlo calculation)
- End-to-end latency (total time from schedule to completion)
- CPU usage during execution
- Memory usage during execution

### Code Location

- **Core script**: `bench-python-project/monte_carlo.py`
- **Airflow DAG**: `data/airflow-dag-code/dags/monte_carlo_*.py`
- **Windmill flow**: `windmill-code/f/flows_scenar_1/`
- **Argo Workflow**: `argo-wf-values/cron_wf_scenar_1_*.yaml`
- **Temporal workflow**: `temporal-code/workflow_scenar_1.py`

---

## Scenario 2A: I/O-Bound (Bash Subprocess)

### Purpose

Test orchestrator performance with **realistic I/O-bound data pipelines** that interact with external services (S3, PostgreSQL, APIs).

This variant uses **bash scripts** that launch Python subprocess, mimicking real-world patterns where workflows shell out to external scripts.

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
- Calls external FastAPI service endpoint: `/sleep/60`
- Waits for 60 seconds (simulates external system dependency)
- **Purpose**: Test external service integration and waiting behavior

#### Task 4: Copy S3 to PostgreSQL
- Reads processed data from S3
- Loads data into PostgreSQL table (`elt.users`)
- **Purpose**: Test database I/O and bulk inserts

### Execution Pattern

- **Sequential execution**: Each task waits for the previous task to complete
- **Bash subprocess**: Python scripts are launched via bash (subprocess overhead)
- **Multiple instances**: Runs 1-12 parallel instances to test concurrency

### Schedule

Runs every **5 minutes** (`*/5 * * * *`) with configurable parallelism

### Code Location

- **Core scripts**: `bench-python-project/task_*.py`
- **Bash wrappers**: Embedded in orchestrator-specific configurations
- **Airflow DAG**: `data/airflow-dag-code/dags/io_bound_scenar_2a_*.py`
- **Windmill flow**: `windmill-code/f/flows_scenar_2a/`
- **Argo Workflow**: `argo-wf-values/cron_wf_scenar_2_a_*.yaml`
- **Temporal workflow**: `temporal-code/workflow_scenar_2_a.py`

---

## Scenario 2B: I/O-Bound (Pure Python)

### Purpose

Same as Scenario 2A but with **pure Python activities** (no bash subprocess overhead).

This allows comparison of:
- Subprocess overhead impact
- Native language execution performance

### Workload Description

Identical to Scenario 2A but implemented as pure Python activities:

1. **Task 1**: Delete S3 & drop tables (pure Python)
2. **Task 2**: S3 ingestion & compute (pure Python)
3. **Task 3**: Wait for external service (pure Python)
4. **Task 4**: Copy S3 to PostgreSQL (pure Python)

### Differences from 2A

| Aspect | Scenario 2A | Scenario 2B |
|--------|-------------|-------------|
| **Execution** | Bash → Python subprocess | Pure Python |
| **Overhead** | Subprocess creation overhead | No subprocess overhead |
| **Use case** | Real-world scripts | Native language activities |

### Schedule

Runs every **5 minutes** (`*/5 * * * *`) with configurable parallelism

### Code Location

- **Core scripts**: `windmill-code/f/python_scripts/task_*_scenar_2_b_*.py`
- **Temporal activities**: `temporal-code/python_scripts/`
- **Windmill flow**: `windmill-code/f/flows_scenar_2b/`
- **Temporal workflow**: `temporal-code/workflow_scenar_2_b.py`

---

## Metrics Collection

All scenarios collect standardized metrics using the Prometheus PushGateway.

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
    "scenario": "scenar_1" | "scenar_2a" | "scenar_2b",
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
| **Subprocess overhead** | No | Yes (bash → Python) | No (pure Python) |
| **Task count** | 1 or 4 | 4 sequential | 4 sequential |
| **Parallelism** | Low | 1-12 instances | 1-12 instances |
| **Runtime** | ~10-30s per task | ~90-120s total | ~90-120s total |

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
