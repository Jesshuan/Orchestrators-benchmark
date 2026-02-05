# Orchestrators Setup Guide

Detailed deployment instructions for all four orchestrators.

---

## Table of Contents

1. [Windmill](#windmill)
2. [Apache Airflow](#apache-airflow)
3. [Argo Workflows](#argo-workflows)
4. [Temporal.io](#temporalio)

---

## Windmill

Windmill is a developer-friendly workflow orchestrator with a "hybrid declarative approach" and design UI, for fast dev iterations during the dev period, and a robust, scalable, 'multi-tenant' orchestrator production platform for the production period.

### Prerequisites

- Windmill CLI (`wmill`) - official installation link

### Deploy Custom PostgreSQL for Windmill

```bash
cd orchestrators-helm-deployments/windmill/postgres-custom
helm install windmill-postgres . -n windmill --create-namespace --values values.yaml
```

Wait for the PostgreSQL pod to be ready:

```bash
kubectl get pods -n windmill
```

---

### Variant 1: Custom Workers (Scenario 1 & 2A)

This variant uses custom workers with bash script activities.

#### Step 1: Add the Windmill Helm repository

```bash
helm repo add windmill https://windmill-labs.github.io/windmill-helm-charts/
helm repo update
```

#### Step 2: Build the custom Docker image

From the root of the project:

```bash
docker build -t windmill-bench-project -f ./docker-orchestrator-factory/windmill-docker-image/Dockerfile .
```

#### Step 3: Load the image to Kind

```bash
kind load docker-image windmill-bench-project:latest -n bench-orchestrator
```

#### Step 4: Deploy Windmill with custom workers

```bash
cd orchestrators-helm-deployments/windmill
helm install mywindmill windmill/windmill -n windmill --values values_variant_1.yaml
```

**Note:** This configuration sets 0 replicas for default workers and uses custom worker groups.

---

### Variant 2: Default Workers (Scenario 2B)

This variant uses default Windmill workers with pure Python activities.

#### Deploy Windmill with default workers

```bash
cd orchestrators-helm-deployments/windmill
helm install mywindmill windmill/windmill -n windmill --values values_variant_2.yaml
```

Or upgrade from Variant 1:

```bash
helm upgrade mywindmill windmill/windmill -n windmill --values values_variant_2.yaml
```

---

### Setup Windmill Workspace and Code

#### Step 1: Access Windmill UI

Port-forward the Windmill server:

```bash
kubectl port-forward -n windmill svc/mywindmill 8000:8000
```

Navigate to: `http://localhost:8000`

**Login credentials:**
- Username: `admin@windmill.dev`
- Password: `changeme`

#### Step 2: Create workspace

Create a new workspace named `bench-orchestrator`. It will be empty initially.

#### Step 3: Add workspace to your local machine

```bash
wmill workspace add
```

Follow the prompts:
- **Name:** `bench-orchestrator`
- **Workspace ID:** `bench-orchestrator`
- **Remote URL:** `http://localhost:8000/`
- **Login method:** Browser (or Token)

#### Step 4: Push scripts and workflows

```bash
cd windmill-code
wmill sync push --include-schedules
```

This uploads:
- Bash scripts
- Python scripts
- Workflow definitions (flows)
- Schedules

#### Step 5: Configure environment variables

**Important:** The `wmill sync push` command may not correctly set environment variables.

For each of the 6 scripts (bash + python), manually verify and set environment variables:

1. Open each script in the Windmill UI
2. Go to **Settings → Runtime → Env**
3. Copy environment variables from the corresponding YAML files in `windmill-code/f/`

Scripts requiring environment variables:
- All bash scripts in `bash_scripts/` folder
- All python scripts in `python_scripts/` folder

---

## Apache Airflow

Apache Airflow with CeleryExecutor (persistent workers).

### Prerequisites

- Apache Airflow Helm chart
- PV/PVC for DAG synchronization

---

### Deploy PVC for DAG Syncing

Create a persistent volume claim to sync DAGs from your local folder to Airflow.

```bash
cd orchestrators-helm-deployments/airflow/pvc-claim
kubectl apply -f pv_pvc_values.yaml
```

Verify the PVC:

```bash
kubectl get pvc -n airflow
```

---

### Variant 1: CeleryExecutor (Scenario 1, 2A & 2B)

This variant uses CeleryExecutor with permanently running workers.

#### Step 1: Add the Airflow Helm repository

```bash
helm repo add apache-airflow https://airflow.apache.org
helm repo update
```

#### Step 2: Build the custom Docker image

From the root of the project:

```bash
docker build -t airflow-bench-project -f ./docker-orchestrator-factory/airflow-docker-image/Dockerfile .
```

#### Step 3: Load the image to Kind

```bash
kind load docker-image airflow-bench-project:latest -n bench-orchestrator
```

#### Step 4: Deploy Airflow

```bash
cd orchestrators-helm-deployments/airflow
helm install airflow3 apache-airflow/airflow -n airflow --values values_celery_variant_1.yaml
```

This deploys Airflow 3.0.2 with:
- CeleryExecutor
- Custom worker image with benchmark scripts
- PVC for DAG synchronization

#### Step 5: Verify deployment

```bash
kubectl get pods -n airflow
```

Wait for all pods to be in `Running` state (this may take a few minutes).

---

### Access Airflow WebUI

Port-forward the Airflow webserver:

```bash
kubectl port-forward -n airflow svc/airflow3-webserver 8080:8080
```

Navigate to: `http://localhost:8080`

**Login credentials:**
- Username: `admin`
- Password: `admin`

Your DAGs should be automatically loaded thanks to the volume mapping:
```
local machine → kind node → airflow instances (via k8s PV/PVC)
```

---

## Argo Workflows

Kubernetes-native workflow engine with ephemeral pods.

### Prerequisites

- Argo Workflows CLI (`argo`)
- Multi-namespace setup (multi-tenancy)

---

### Step 1: Create namespaces

```bash
kubectl create namespace argo-wf
kubectl create namespace team-a
```

**Note:** We use a multi-tenancy setup where `team-a` is a managed namespace for workflows.

---

### Step 2: Add the Argo Helm repository

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
```

---

### Step 3: Deploy Argo Workflows

```bash
cd orchestrators-helm-deployments/argo_workflow
helm install argo-wf argo/argo-workflows --version 0.45.26 -n argo-wf --values values.yaml
```

This deploys Argo with:
- Multi-tenancy enabled (managed namespace mode)
- Auth mode: `client` (for testing)
- Controller parallelism: 4

---

### Step 4: Install the Argo CLI

Download the Argo CLI from the official releases page:

[https://github.com/argoproj/argo-workflows/releases/](https://github.com/argoproj/argo-workflows/releases/)

For Linux:
```bash
curl -sLO https://github.com/argoproj/argo-workflows/releases/download/v3.5.0/argo-linux-amd64.gz
gunzip argo-linux-amd64.gz
chmod +x argo-linux-amd64
sudo mv argo-linux-amd64 /usr/local/bin/argo
```

---

### Step 5: Setup RBAC for managed namespace

Deploy custom service accounts and RBAC for the `team-a` namespace.

```bash
cd argo-wf-values/argo-custom-namespace-setup
helm install argo-custom-namespace-setup . -n team-a --values values_team_a.yaml
```

This creates:
- **Executor service account** (`team-a-awf-executor`) - For workflow execution
- **Ops/Maintainer service account** (`team-a-ops-maintainer`) - For human operators

---

### Step 6: Test workflow execution

Test with the executor service account:

```bash
cd argo-wf-values/workflow-test
```

```bash
argo submit wf-hello-world.yaml \
  --serviceaccount team-a-awf-executor \
  -n team-a \
  --watch
```

Test with the ops/maintainer service account:

```bash
argo submit wf-hello-world.yaml \
  --serviceaccount team-a-ops-maintainer \
  -n team-a \
  --watch
```

Check the pod logs with kubectl or k9s to verify execution.

---

### Step 7: Access Argo UI

Port-forward the Argo server:

```bash
kubectl port-forward -n argo-wf svc/argo-wf-argo-workflows-server 2746:2746
```

Navigate to: `http://localhost:2746`

---

### Step 8: Get authentication token for UI

Get the token for the `team-a-ops-maintainer` user:

```bash
ARGO_TOKEN="Bearer $(kubectl get secret team-a-ops-maintainer-secret-token -n team-a -o=jsonpath='{.data.token}' | base64 --decode)"
echo $ARGO_TOKEN
```

Copy the token and paste it on the Argo UI login page (client usage field).

Retrieve the last workflows executed... test it again with the "Re-Submit" option...

---

### Step 9: Deploy workflow templates

Deploy reusable workflow templates:

```bash
cd argo-wf-values/argo-workflow-template
helm install argo-workflow-tasks-template . --values values.yaml
```

---

### Step 10: Deploy CronWorkflows (Scenario 1, 2A)

Deploy scheduled workflows for benchmarking:

Example :


```bash
cd argo-wf-values/cron-workflow-generation
argo cron create ./scenar_2/cron_wf_scenar_2_a_io_bound_4_tasks_11.yaml -n team-a
```

Repeat for other CronWorkflow definitions as needed.

FOr simplicity (in this benchmark study), sorry, but you have to generate / delete each cron workflow manually.

**Note** : Scenario 2 b does'nt exist for Argo Workflow, cause all the task have to be launch as a 'bash' scripts, not python Operators or python activities, etc.

---

## Temporal.io

Durable execution platform with distributed workflows.

### Prerequisites

- Custom worker Docker image
- PostgreSQL database for Temporal server
- PV/PVC for schedule definitions

---

### Build Custom Worker Image

#### Variant 1: Bash Script Activities (Scenario 1, 2A)

Workers launch Python scripts via bash subprocess:

```bash
docker build -t temporal-bench-worker \
  -f ./docker-orchestrator-factory/temporal-docker-image/Dockerfile . \
  --build-arg WORKER_SCRIPT=/app/temporal-worker/src/run_worker.py
```

#### Variant 2: Pure Python Activities (Scenario 2B)

Workers use pure Python activities:

```bash
docker build -t temporal-bench-worker \
  -f ./docker-orchestrator-factory/temporal-docker-image/Dockerfile . \
  --build-arg WORKER_SCRIPT=/app/temporal-worker/src/run_worker_2.py
```

Load the image to Kind:

```bash
kind load docker-image temporal-bench-worker:latest -n bench-orchestrator
```

---

### Deploy Custom PostgreSQL for Temporal

```bash
cd orchestrators-helm-deployments/temporal/postgres-custom
helm install custom-temporal-postgres-db . -n temporal --create-namespace --values values.yaml
```

Wait for PostgreSQL to be ready, then connect to the database and create the visibility database:

```bash
kubectl exec -it -n temporal <postgres-pod-name> -- psql -U temporal_user -d postgres
```

Inside the PostgreSQL shell:

```sql
CREATE DATABASE temporal_visibility WITH OWNER=temporal_user;
\q
```

---

### Deploy Temporal Server

```bash
cd orchestrators-helm-deployments/temporal
helm install temporal temporal \
  --repo https://go.temporal.io/helm-charts \
  --version '>=1.0.0-0' \
  -n temporal \
  -f values.yaml \
  --timeout 900s
```

This deploys the Temporal server with PostgreSQL backend.

---

### Create PVC for Schedule Definitions

```bash
cd orchestrators-helm-deployments/temporal/pvc-claim
kubectl apply -f pv_pvc_values.yaml -n temporal
```

This PVC mounts the `data/temporal-schedules/` directory for schedule JSON files.

---

### Deploy Temporal Workers

#### Variant 1: Bash Script Activities (Scenario 1A, 2A)

```bash
cd orchestrators-helm-deployments/temporal/worker-deployment
helm install temporal-workers . -n temporal --values values_variant_a.yaml
```

#### Variant 2: Pure Python Activities (Scenario 2B)

```bash
cd orchestrators-helm-deployments/temporal/worker-deployment
helm install temporal-workers . -n temporal --values values_variant_a.yaml
```

Or upgrade from Variant 1:

```bash
helm upgrade temporal-workers . -n temporal --values values_variant_b.yaml
```

---

### Generate Temporal Schedules

Use Kubernetes jobs to upload schedule definitions to the Temporal server.

```bash
cd orchestrators-helm-deployments/temporal/schedules-jobs-tools
```

Choose your scenario and apply the corresponding job:

**Example for Scenario 1A:**
```bash
kubectl apply -f create_schedule_scenar_1_a.yaml -n temporal
```

Check the job logs:

```bash
kubectl logs -n temporal job/temporal-generate-schedules-scenar-1
```

The schedules will be visible in the Temporal WebUI and are **paused by default**. Unpause them to start execution.

---

### Access Temporal WebUI

Port-forward the Temporal web UI:

```bash
kubectl port-forward -n temporal svc/temporal-web 8080:8080
```

Navigate to: `http://localhost:8080`

---

## Summary

You've now deployed all four orchestrators:

| Orchestrator | Namespace | WebUI Port | Access |
|--------------|-----------|------------|--------|
| **Windmill** | windmill | 8000 | `http://localhost:8000` |
| **Airflow** | airflow | 8080 | `http://localhost:8080` |
| **Argo Workflows** | argo-wf, team-a | 2746 | `http://localhost:2746` |
| **Temporal.io** | temporal | 8088 | `http://localhost:8088` |

---

## Next Steps

**[Benchmark Scenarios Guide](SCENARIOS.md)** - Learn about the benchmark scenarios and how to run them

**[Observability Setup](OBSERVABILITY.md)** - Configure monitoring and view metrics

---

## Troubleshooting

If you encounter issues, see the **[Troubleshooting Guide](TROUBLESHOOTING.md)**.