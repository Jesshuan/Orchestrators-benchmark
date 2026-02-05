# Results Analysis

Analyze benchmark results using Jupyter notebooks and CSV data.

---

## Table of Contents

1. [Overview](#overview)
2. [Results Location](#results-location)
3. [Using Jupyter Notebooks](#using-jupyter-notebooks)
4. [CSV Data Structure](#csv-data-structure)
5. [Analysis Examples](#analysis-examples)
6. [Visualization Tips](#visualization-tips)
7. [Comparing Orchestrators](#comparing-orchestrators)

---

## Overview

The benchmark collects comprehensive metrics and stores them in CSV format for analysis. Use the provided Jupyter notebooks to visualize and compare orchestrator performance.

**Analysis workflow:**
1. Run benchmarks and collect metrics
2. Export metrics from Prometheus to CSV
3. Load CSV data in Jupyter notebooks
4. Generate visualizations and comparisons
5. Draw conclusions about orchestrator performance

---

## Results Location

### CSV Files

**Primary results file:**
```
benchmark-results-analysis/result/bench_raw_results.csv
```

**Additional result files:**
- `bench_raw_results_2.csv` - Secondary results (if multiple runs)
- `bench_raw_results_temp.csv` - Temporary results during collection

### Jupyter Notebooks

**Analysis notebook:**
```
benchmark-results-analysis/results_dynamic_chart.ipynb
```

This notebook provides:
- Interactive data loading
- Dynamic charts and visualizations
- Statistical analysis
- Orchestrator comparison

---

## Using Jupyter Notebooks

### Step 1: Install dependencies

Create a Python virtual environment and install required packages:

```bash
cd benchmark-results-analysis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install jupyter pandas matplotlib seaborn numpy
```

### Step 2: Launch Jupyter

```bash
jupyter notebook results_dynamic_chart.ipynb
```

This opens the notebook in your default browser.

### Step 3: Run the notebook

- Click **Cell** → **Run All** to execute all cells
- Or run cells individually with `Shift + Enter`

### Step 4: Explore visualizations

The notebook generates:
- **Line charts** - Metrics over time
- **Bar charts** - Orchestrator comparisons
- **Heatmaps** - Resource usage patterns
- **Box plots** - Statistical distributions
- **Scatter plots** - Correlation analysis

---

## CSV Data Structure

### Column Definitions

| Column | Description | Example Values |
|--------|-------------|----------------|
| `orchestrator` | Orchestrator name | airflow, argo, windmill, temporal |
| `scenario` | Benchmark scenario | scenar_1, scenar_2a, scenar_2b |
| `variant` | Scenario variant | 1_task, 4_tasks, bash, python |
| `workflow_number` | Workflow instance | 1, 2, ..., 12 |
| `task` | Task identifier | task_1, task_2, task_3, task_4 |
| `scheduling_delay_seconds` | Scheduling delay | 0.5, 1.2, 5.3 |
| `execution_duration_seconds` | Execution time | 10.5, 25.3, 40.1 |
| `end_to_end_latency_seconds` | Total latency | 11.0, 26.5, 45.4 |
| `cpu_mean_permanent` | Avg CPU (permanent pods) | 0.15, 0.25 |
| `cpu_max_permanent` | Max CPU (permanent pods) | 0.30, 0.50 |
| `cpu_mean_worker` | Avg CPU (worker pods) | 0.80, 1.50 |
| `cpu_max_worker` | Max CPU (worker pods) | 1.00, 2.00 |
| `memory_mean_permanent_mb` | Avg memory (permanent) | 256, 512 |
| `memory_max_permanent_mb` | Max memory (permanent) | 300, 600 |
| `memory_mean_worker_mb` | Avg memory (worker) | 128, 256 |
| `memory_max_worker_mb` | Max memory (worker) | 200, 400 |
| `timestamp` | Collection timestamp | 2025-01-18T10:30:00Z |

### Sample Data

```csv
orchestrator,scenario,variant,workflow_number,task,scheduling_delay_seconds,execution_duration_seconds,end_to_end_latency_seconds,cpu_mean_permanent,memory_mean_permanent_mb
airflow,scenar_1,1_task,1,task_1,0.5,10.2,10.7,0.15,256
argo,scenar_1,1_task,1,task_1,0.3,9.8,10.1,0.10,128
windmill,scenar_1,1_task,1,task_1,0.4,10.5,10.9,0.12,200
temporal,scenar_1,1_task,1,task_1,0.6,10.3,10.9,0.18,300
```

---

## Analysis Examples

### Example 1: Compare Scheduling Delays

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('result/bench_raw_results.csv')

# Filter Scenario 1, 1-task variant
df_scenar1 = df[(df['scenario'] == 'scenar_1') & (df['variant'] == '1_task')]

# Group by orchestrator and calculate mean
scheduling_delay = df_scenar1.groupby('orchestrator')['scheduling_delay_seconds'].mean()

# Plot
scheduling_delay.plot(kind='bar', color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A'])
plt.title('Average Scheduling Delay - Scenario 1 (1 Task)')
plt.ylabel('Seconds')
plt.xlabel('Orchestrator')
plt.tight_layout()
plt.show()
```

---

### Example 2: Execution Duration Over Time

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('result/bench_raw_results.csv')

# Convert timestamp to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Filter Scenario 2A
df_scenar2a = df[(df['scenario'] == 'scenar_2a') & (df['task'] == 'task_1')]

# Plot for each orchestrator
for orchestrator in df_scenar2a['orchestrator'].unique():
    df_orch = df_scenar2a[df_scenar2a['orchestrator'] == orchestrator]
    plt.plot(df_orch['timestamp'], df_orch['execution_duration_seconds'],
             label=orchestrator, marker='o')

plt.title('Execution Duration Over Time - Scenario 2A (Task 1)')
plt.xlabel('Time')
plt.ylabel('Seconds')
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

---

### Example 3: Resource Usage Comparison

```python
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('result/bench_raw_results.csv')

# Calculate total CPU (permanent + worker)
df['total_cpu_mean'] = df['cpu_mean_permanent'] + df['cpu_mean_worker']

# Group by orchestrator and scenario
resource_usage = df.groupby(['orchestrator', 'scenario'])['total_cpu_mean'].mean().reset_index()

# Pivot for heatmap
heatmap_data = resource_usage.pivot(index='orchestrator', columns='scenario', values='total_cpu_mean')

# Plot heatmap
sns.heatmap(heatmap_data, annot=True, fmt='.2f', cmap='YlOrRd')
plt.title('Average CPU Usage by Orchestrator and Scenario')
plt.tight_layout()
plt.show()
```

---

### Example 4: Statistical Summary

```python
import pandas as pd

# Load data
df = pd.read_csv('result/bench_raw_results.csv')

# Group by orchestrator and calculate statistics
summary = df.groupby('orchestrator').agg({
    'scheduling_delay_seconds': ['mean', 'std', 'min', 'max'],
    'execution_duration_seconds': ['mean', 'std', 'min', 'max'],
    'end_to_end_latency_seconds': ['mean', 'std', 'min', 'max']
})

print(summary)
```

---

### Example 5: Percentile Analysis

```python
import pandas as pd

# Load data
df = pd.read_csv('result/bench_raw_results.csv')

# Calculate percentiles for end-to-end latency
percentiles = df.groupby('orchestrator')['end_to_end_latency_seconds'].quantile([0.5, 0.95, 0.99])

print(percentiles)
```

---

## Visualization Tips

### 1. Use Consistent Colors

Assign consistent colors to each orchestrator:

```python
colors = {
    'airflow': '#FF6B6B',    # Red
    'argo': '#4ECDC4',       # Teal
    'windmill': '#45B7D1',   # Blue
    'temporal': '#FFA07A'    # Orange
}
```

### 2. Add Error Bars

Show variability in metrics:

```python
import pandas as pd
import matplotlib.pyplot as plt

# Group by orchestrator and calculate mean + std
grouped = df.groupby('orchestrator')['execution_duration_seconds'].agg(['mean', 'std'])

# Plot with error bars
grouped['mean'].plot(kind='bar', yerr=grouped['std'], capsize=5)
plt.title('Execution Duration with Standard Deviation')
plt.ylabel('Seconds')
plt.show()
```

### 3. Use Subplots for Multiple Metrics

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Scheduling delay
df.groupby('orchestrator')['scheduling_delay_seconds'].mean().plot(ax=axes[0, 0], kind='bar')
axes[0, 0].set_title('Scheduling Delay')

# Execution duration
df.groupby('orchestrator')['execution_duration_seconds'].mean().plot(ax=axes[0, 1], kind='bar')
axes[0, 1].set_title('Execution Duration')

# CPU usage
df.groupby('orchestrator')['cpu_mean_worker'].mean().plot(ax=axes[1, 0], kind='bar')
axes[1, 0].set_title('CPU Usage (Workers)')

# Memory usage
df.groupby('orchestrator')['memory_mean_worker_mb'].mean().plot(ax=axes[1, 1], kind='bar')
axes[1, 1].set_title('Memory Usage (Workers)')

plt.tight_layout()
plt.show()
```

### 4. Interactive Plots with Plotly

```python
import pandas as pd
import plotly.express as px

# Load data
df = pd.read_csv('result/bench_raw_results.csv')

# Interactive line chart
fig = px.line(df, x='timestamp', y='end_to_end_latency_seconds',
              color='orchestrator', facet_col='scenario',
              title='End-to-End Latency by Orchestrator and Scenario')
fig.show()
```

---

## Comparing Orchestrators

### Key Metrics to Compare

#### 1. Scheduling Efficiency
- **Metric:** `scheduling_delay_seconds`
- **Lower is better**
- **Insight:** Measures scheduler overhead and responsiveness

#### 2. Execution Performance
- **Metric:** `execution_duration_seconds`
- **Lower is better** (for same workload)
- **Insight:** Measures task execution overhead (e.g., subprocess creation)

#### 3. End-to-End Latency
- **Metric:** `end_to_end_latency_seconds`
- **Lower is better**
- **Insight:** Total user-perceived latency

#### 4. Resource Efficiency
- **Metrics:** `cpu_mean_*`, `memory_mean_*`
- **Lower is better** (for same workload)
- **Insight:** Cost and scalability implications

#### 5. Consistency
- **Metric:** Standard deviation of metrics
- **Lower is better**
- **Insight:** Predictability and reliability

---

### Comparison Template

```python
import pandas as pd

# Load data
df = pd.read_csv('result/bench_raw_results.csv')

# Filter for a specific scenario
df_scenario = df[df['scenario'] == 'scenar_1']

# Calculate comparison metrics
comparison = df_scenario.groupby('orchestrator').agg({
    'scheduling_delay_seconds': ['mean', 'std'],
    'execution_duration_seconds': ['mean', 'std'],
    'end_to_end_latency_seconds': ['mean', 'std'],
    'cpu_mean_worker': 'mean',
    'memory_mean_worker_mb': 'mean'
})

# Display comparison
print(comparison)

# Rank orchestrators by end-to-end latency
ranking = df_scenario.groupby('orchestrator')['end_to_end_latency_seconds'].mean().sort_values()
print("\nOrchestrator Ranking (End-to-End Latency):")
print(ranking)
```

---

## Exporting Results

### Export to PDF

```python
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

with PdfPages('benchmark_results.pdf') as pdf:
    # Generate plots
    fig1 = plt.figure()
    # ... plot code ...
    pdf.savefig(fig1)

    fig2 = plt.figure()
    # ... plot code ...
    pdf.savefig(fig2)
```

### Export to HTML Report

```python
import pandas as pd

# Load data
df = pd.read_csv('result/bench_raw_results.csv')

# Generate summary statistics
summary = df.groupby('orchestrator').describe()

# Export to HTML
summary.to_html('benchmark_report.html')
```

---

## Next Steps

**[Troubleshooting Guide](TROUBLESHOOTING.md)** - Resolve common issues

**[Architecture Details](ARCHITECTURE.md)** - Understand the technical design

---

## Additional Resources

- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Matplotlib Gallery](https://matplotlib.org/stable/gallery/index.html)
- [Seaborn Tutorial](https://seaborn.pydata.org/tutorial.html)
- [Plotly Python](https://plotly.com/python/)
