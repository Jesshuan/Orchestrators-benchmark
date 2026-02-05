# Observability Setup

Configure and use the monitoring stack to collect and visualize benchmark metrics.

---

## Table of Contents

1. [Overview](#overview)
2. [Components](#components)
3. [Accessing Monitoring Tools](#accessing-monitoring-tools)
4. [Grafana Dashboards](#grafana-dashboards)
5. [Prometheus Queries](#prometheus-queries)
6. [Metrics Reference](#metrics-reference)
7. [Troubleshooting Metrics](#troubleshooting-metrics)

---

## Overview

The observability stack provides comprehensive monitoring for the benchmark:

- **Prometheus** - Metrics collection and storage
- **Grafana** - Visualization and dashboards
- **PushGateway** - Receives metrics from benchmark tasks

```
┌─────────────┐     push      ┌──────────────┐
│ Benchmark   │─────────────→ │ PushGateway  │
│   Tasks     │               │   :9091      │
└─────────────┘               └──────┬───────┘
                                     │
                                     │ scrape (5s)
                                     ▼
                              ┌──────────────┐
                              │  Prometheus  │
                              │   :9090      │
                              └──────┬───────┘
                                     │
                                     │ query
                                     ▼
                              ┌──────────────┐
                              │   Grafana    │
                              │   :3000      │
                              └──────────────┘
```

---

## Components

### Prometheus

**Purpose:** Time-series database for metrics storage and querying

**Configuration:**
- **Scrape interval:** 5 seconds
- **Retention:** 24 hours
- **Storage:** Persistent volume (if configured)

**Scrape targets:**
- Kubernetes pods (via ServiceMonitor)
- PushGateway (for custom benchmark metrics)
- Node exporters (for system metrics)

**Access:** Port-forward to access Prometheus UI:
```bash
kubectl port-forward -n observ-stack svc/observability-stack-kube-prom-prometheus 9090:9090
```
Navigate to: `http://localhost:9090`

---

### Grafana

**Purpose:** Visualization and dashboard platform

**Configuration:**
- Pre-configured data sources (Prometheus)
- Custom dashboards for benchmark metrics
- Admin service account for API access

**Access:** Port-forward to access Grafana UI:
```bash
kubectl port-forward -n observ-stack svc/observability-stack-grafana 3000:80
```
Navigate to: `http://localhost:3000`

**Default credentials:**
- Username: `admin`
- Password: `admin` (change on first login)

---

### PushGateway

**Purpose:** Receive metrics from short-lived tasks (benchmark jobs)

**Why PushGateway?**
- Benchmark tasks are ephemeral (finish quickly)
- Prometheus scraping may miss short-lived metrics
- PushGateway acts as a buffer for batch metrics

**Endpoint:** `http://prometheus-pushgateway.observ-stack.svc.cluster.local:9091`

**Access:** Port-forward to view metrics:
```bash
kubectl port-forward -n observ-stack svc/prometheus-pushgateway 9091:9091
```
Navigate to: `http://localhost:9091`

---

## Accessing Monitoring Tools

### Port-Forward Commands

Create port-forwards for all monitoring tools:

```bash
# Prometheus
kubectl port-forward -n observ-stack svc/observability-stack-kube-prom-prometheus 9090:9090 &

# Grafana
kubectl port-forward -n observ-stack svc/observability-stack-grafana 3000:80 &

# PushGateway
kubectl port-forward -n observ-stack svc/prometheus-pushgateway 9091:9091 &
```

**Tip:** Use `&` to run in the background, or open separate terminal windows.

### Stop Port-Forwards

```bash
# Find port-forward processes
ps aux | grep port-forward

# Kill specific port-forward
kill <PID>

# Or kill all port-forwards
pkill -f "port-forward"
```

---

## Grafana Dashboards

### Pre-configured Dashboard

The benchmark includes a pre-configured Grafana dashboard: **Orchestrator Benchmark Metrics**

**Panels:**
1. **Scheduling Delay** - Time from schedule to start (per orchestrator)
2. **Execution Duration** - Task execution time (per orchestrator)
3. **End-to-End Latency** - Total time from schedule to completion
4. **CPU Usage** - CPU consumption (permanent vs. worker pods)
5. **Memory Usage** - Memory consumption (permanent vs. worker pods)
6. **Task Success Rate** - Percentage of successful task executions
7. **Throughput** - Tasks completed per minute

**Filters:**
- Orchestrator (Airflow, Argo, Windmill, Temporal)
- Scenario (1, 2A, 2B)
- Workflow instance (1-12)
- Task (task_1, task_2, task_3, task_4)

---

### Viewing the Dashboard

1. Open Grafana: `http://localhost:3000`
2. Navigate to **Dashboards** (left sidebar)
3. Search for "Orchestrator Benchmark"
4. Click on the dashboard to open it

**Dashboard features:**
- Time range selector (default: last 1 hour)
- Variable dropdowns for filtering
- Refresh interval (auto-refresh every 5s)
- Panel zoom and drill-down

---

### Creating Custom Dashboards

To create your own dashboard:

1. Click **+ Create** → **Dashboard**
2. Add a new panel
3. Select Prometheus as the data source
4. Enter a PromQL query (see examples below)
5. Configure visualization (graph, gauge, table, etc.)
6. Save the dashboard

---

## Prometheus Queries

### Useful PromQL Queries

#### Scheduling Delay by Orchestrator

```promql
avg(benchmark_scheduling_delay_seconds) by (orchestrator)
```

#### 95th Percentile Execution Duration

```promql
histogram_quantile(0.95,
  rate(benchmark_execution_duration_seconds_bucket[5m])
) by (orchestrator, scenario)
```

#### End-to-End Latency Over Time

```promql
benchmark_end_to_end_latency_seconds{scenario="scenar_2a"}
```

#### CPU Usage by Orchestrator

```promql
sum(rate(container_cpu_usage_seconds_total{namespace=~"airflow|windmill|argo-wf|temporal"}[5m]))
by (namespace)
```

#### Memory Usage by Orchestrator

```promql
sum(container_memory_working_set_bytes{namespace=~"airflow|windmill|argo-wf|temporal"})
by (namespace) / 1024 / 1024
```

#### Task Success Rate

```promql
sum(rate(benchmark_execution_duration_seconds_count[5m])) by (orchestrator)
```

#### Compare Scenario Performance

```promql
avg(benchmark_execution_duration_seconds{scenario="scenar_1"}) by (orchestrator)
vs
avg(benchmark_execution_duration_seconds{scenario="scenar_2a"}) by (orchestrator)
```

---

## Metrics Reference

### Benchmark Metrics

These metrics are pushed by benchmark tasks to PushGateway.

#### `benchmark_scheduling_delay_seconds`

**Type:** Gauge
**Description:** Delay from scheduled execution time to actual start time
**Labels:**
- `scenario` - Benchmark scenario (scenar_1, scenar_2a, scenar_2b)
- `workflow_number` - Workflow instance number (1-12)
- `task` - Task identifier (task_1, task_2, task_3, task_4)
- `orchestrator` - Orchestrator name (airflow, argo, windmill, temporal)

**Interpretation:**
- **Low values (< 1s):** Efficient scheduling
- **High values (> 5s):** Scheduling bottleneck or resource contention

---

#### `benchmark_execution_duration_seconds`

**Type:** Gauge
**Description:** Time taken to execute the task logic
**Labels:** Same as above

**Interpretation:**
- **Scenario 1:** Expect 10-30s (CPU-intensive)
- **Scenario 2A/2B:** Expect 20-40s per task

---

#### `benchmark_end_to_end_latency_seconds`

**Type:** Gauge
**Description:** Total time from schedule to completion
**Labels:** Same as above

**Formula:** `end_to_end_latency = scheduling_delay + execution_duration`

**Interpretation:**
- Measures total user-perceived latency
- Combines scheduling overhead and execution time

---

### System Metrics

These metrics are automatically collected by Prometheus from Kubernetes.

#### CPU Metrics

- `container_cpu_usage_seconds_total` - Total CPU time used by container
- `node_cpu_seconds_total` - CPU time per node

#### Memory Metrics

- `container_memory_working_set_bytes` - Current memory usage
- `container_memory_rss` - Resident memory
- `node_memory_MemAvailable_bytes` - Available memory on node

#### Pod Metrics

- `kube_pod_status_phase` - Pod phase (Running, Pending, Failed)
- `kube_pod_container_resource_requests` - Resource requests
- `kube_pod_container_resource_limits` - Resource limits

---

## Troubleshooting Metrics

### Metrics Not Appearing in Grafana

**Symptoms:** Dashboard panels show "No data" or empty graphs

**Troubleshooting steps:**

1. **Check if tasks are running:**
   ```bash
   kubectl get pods -n airflow  # or windmill, argo-wf, temporal
   ```

2. **Verify PushGateway is receiving metrics:**
   - Open PushGateway UI: `http://localhost:9091`
   - Look for `benchmark_*` metrics
   - Check the labels match your filters

3. **Check Prometheus is scraping PushGateway:**
   - Open Prometheus UI: `http://localhost:9090`
   - Go to **Status** → **Targets**
   - Verify `prometheus-pushgateway` target is UP
   - Check scrape interval and last scrape time

4. **Query metrics directly in Prometheus:**
   ```promql
   {__name__=~"benchmark_.*"}
   ```
   - If no results, metrics aren't being pushed
   - If results appear, issue is with Grafana query or dashboard

5. **Check task logs for errors:**
   ```bash
   kubectl logs -n <namespace> <pod-name>
   ```
   - Look for errors related to PushGateway connection
   - Verify environment variables (PUSHGATEWAY_URL)

---

### High Scheduling Delays

**Symptoms:** `benchmark_scheduling_delay_seconds` > 10s

**Possible causes:**
- Resource contention (CPU/memory limits)
- Too many concurrent workflows
- Slow orchestrator scheduler
- Worker pods not scaling fast enough

**Solutions:**
- Reduce parallelism (fewer workflow instances)
- Increase resource limits for orchestrator pods
- Scale up worker replicas
- Check orchestrator-specific logs for bottlenecks

---

### Missing CPU/Memory Metrics

**Symptoms:** CPU/Memory panels show no data

**Troubleshooting steps:**

1. **Check if metrics-server is installed:**
   ```bash
   kubectl get deployment metrics-server -n kube-system
   ```

2. **Verify ServiceMonitor is configured:**
   ```bash
   kubectl get servicemonitor -n observ-stack
   ```

3. **Check Prometheus targets:**
   - Open Prometheus UI
   - Go to **Status** → **Targets**
   - Look for Kubernetes pod monitoring targets

4. **Verify namespace labels:**
   ```bash
   kubectl get namespace <namespace> --show-labels
   ```
   - Ensure namespaces have labels for Prometheus scraping

---

### PushGateway Not Accessible

**Symptoms:** Tasks log errors like "Connection refused" to PushGateway

**Troubleshooting steps:**

1. **Check PushGateway pod status:**
   ```bash
   kubectl get pods -n observ-stack -l app=prometheus-pushgateway
   ```

2. **Verify service exists:**
   ```bash
   kubectl get svc -n observ-stack prometheus-pushgateway
   ```

3. **Test connectivity from a pod:**
   ```bash
   kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
     curl http://prometheus-pushgateway.observ-stack.svc.cluster.local:9091/metrics
   ```

4. **Check environment variable in task pods:**
   ```bash
   kubectl exec -n <namespace> <pod-name> -- env | grep PUSHGATEWAY
   ```
   - Should show: `PUSHGATEWAY_URL=prometheus-pushgateway.observ-stack.svc.cluster.local:9091`

---

## Next Steps

**[Results Analysis Guide](RESULTS.md)** - Analyze collected metrics using Jupyter notebooks

**[Architecture Details](ARCHITECTURE.md)** - Understand the technical architecture

---

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Cheat Sheet](https://promlabs.com/promql-cheat-sheet/)
- [PushGateway Best Practices](https://prometheus.io/docs/practices/pushing/)
