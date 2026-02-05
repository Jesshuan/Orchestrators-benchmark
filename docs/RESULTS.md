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

**TODO**

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
pip install jupyter pandas numpy plotly-express
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
**TODO**
- **Bar charts** - Orchestrator comparisons


---
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


## Comparing Orchestrators

**TODO**

### Key Metrics to Compare

#### 1. Scheduling Efficiency
- **Metric:** `scheduling_delay_seconds`
- **Lower is better**
- **Insight:** Measures scheduler overhead and responsiveness

#### 2. Execution Performance
- **Metric:** `execution_duration_seconds`
- **Lower is better** (for same workload)
- **Insight:** Measures task execution overhead (e.g., subprocess creation)


#### 4. Resource Efficiency
- **Metrics:** `cpu_mean_*`, `memory_mean_*`
- **Lower is better** (for same workload)
- **Insight:** Cost and scalability implications

#### 5. Consistency
- **Metric:** Standard deviation of metrics
- **Lower is better**
- **Insight:** Predictability and reliability

---



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

**TODO**

**[Troubleshooting Guide](TROUBLESHOOTING.md)** - Resolve common issues

**[Architecture Details](ARCHITECTURE.md)** - Understand the technical design

---

## Additional Resources

- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Matplotlib Gallery](https://matplotlib.org/stable/gallery/index.html)
- [Seaborn Tutorial](https://seaborn.pydata.org/tutorial.html)
- [Plotly Python](https://plotly.com/python/)
