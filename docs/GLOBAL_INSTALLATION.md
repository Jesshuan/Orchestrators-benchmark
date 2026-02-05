# Installation Guide

Complete step-by-step instructions to set up the benchmark environment.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Create the Kind Cluster](#create-the-kind-cluster)
3. [Observability Stack Setup](#observability-stack-setup)
4. [Grafana Configuration](#grafana-configuration)
5. [Generate Test Data](#generate-test-data)
6. [Deploy External Services](#deploy-external-services)
7. [Deploy FastAPI Service](#deploy-fastapi-service)
8. [Next Steps](#next-steps)

---

## Prerequisites

Ensure you have the following tools installed:

| Tool | Version | Purpose |
|------|---------|---------|
| **Docker** | Latest | Container runtime |
| **Kind** | v0.20+ | Local Kubernetes cluster |
| **kubectl** | v1.28+ | Kubernetes CLI |
| **Helm** | v3.x | Package manager for Kubernetes |
| **Python** | 3.11+ | For benchmark tasks and analysis |
| **envsubst** | - | Environment variable substitution (usually pre-installed) |

Optional tools:
- **k9s** - Terminal UI for Kubernetes (recommended for monitoring)
- **grafana-backup** - For importing Grafana dashboards

---

## Create the Kind Cluster

### Step 1: Set the data path

From the root directory of this project:

```bash
export DATA_PATH="${PWD}/data"
```

This variable is used in the Kind cluster configuration to mount local directories.

### Step 2: Create the cluster

```bash
envsubst < config_cluster.yaml | kind create cluster --config=-
```

This command:
- Substitutes environment variables in `config_cluster.yaml`
- Creates a Kind cluster named `bench-orchestrator`
- Configures port mappings (80, 443)
- Mounts the `/data` directory for persistent volumes

### Step 3: Verify the cluster

```bash
kubectl cluster-info
kubectl get nodes
```

You should see your Kind control-plane node in a `Ready` state.

---

## Observability Stack Setup

Deploy Prometheus, Grafana, and PushGateway for metrics collection.

### Step 1: Navigate to the observability stack directory

```bash
cd observability-stack
```

### Step 2: Add Helm repositories

```bash
helm repo add kube-prometheus-stack https://prometheus-community.github.io/helm-charts
helm repo add prometheus-pushgateway https://prometheus-community.github.io/helm-charts
helm repo update
```

### Step 3: Build Helm dependencies

```bash
helm dependency build
```

This downloads the required charts defined in `Chart.yaml`.

### Step 4: Install the observability stack

```bash
helm install observability-stack . -n observ-stack --create-namespace --values values.yaml
```

This deploys:
- **Prometheus** (scrape interval: 5 seconds, retention: 24 hours)
- **Grafana** (for visualization)
- **PushGateway** (for custom metrics)

### Step 5: Verify the deployment

```bash
kubectl get pods -n observ-stack
```

Wait until all pods are in `Running` state.

---

## Grafana Configuration

### Step 1: Port-forward Grafana

```bash
kubectl port-forward -n observ-stack svc/observability-stack-grafana 3000:80
```

### Step 2: Access Grafana

Open your browser and navigate to: `http://localhost:3000`

**Initial credentials:**
- Username: `admin`
- Password: `admin`

You'll be prompted to change the password on first login.

### Step 3: Generate an admin token

1. Click on your profile icon (top-right corner)
2. Go to **Profile**
3. Navigate to **Service Accounts**
4. Create a new service account with **Admin** role
5. Generate a token and save it securely

### Step 4: Install grafana-backup tool

```bash
# Create a Python virtual environment
python -m venv grafana-env
source grafana-env/bin/activate  # On Windows: grafana-env\Scripts\activate

# Install grafana-backup
pip install grafana-backup
```

### Step 5: Set environment variables

```bash
export GRAFANA_URL=http://localhost:3000
export GRAFANA_TOKEN=your_admin_token_here
```

Replace `your_admin_token_here` with the token generated in Step 3.

### Step 6: Restore Grafana dashboards

```bash
cd grafana-backup
grafana-backup restore _OUTPUT_/*.gz
```

This imports the pre-configured dashboard for viewing orchestrator metrics.

---

## Generate Test Data

Generate a fake parquet data file using FakeLake.

### Step 1: Navigate to the data generation directory

```bash
cd fake_data_generation
```

### Step 2: Extract FakeLake

```bash
tar -xvf fakelake-x86_64-unknown-linux-musl.tar.gz
```

### Step 3: Generate the users.parquet file

```bash
./fakelake generate users.yaml
```

This creates a `users.parquet` file in the same directory. This file will be uploaded to MinIO S3 later.

**Note:** Credit to [FakeLake](https://github.com/dacort/fakelake) for the data generation tool.

---

## Deploy External Services

Deploy PostgreSQL and MinIO S3 for data storage.

### Step 1: Navigate to the external databases directory

```bash
cd external_databases
```

### Step 2: Install the external databases

```bash
helm install external-db . -n external-db --create-namespace --values values.yaml
```

This deploys:
- **PostgreSQL 15** (used by all orchestrators and for benchmark data)
- **MinIO S3** (S3-compatible object storage)

### Step 3: Verify the deployment

```bash
kubectl get pods -n external-db
```

### Step 4: Configure MinIO S3

#### Find the MinIO WebUI port

```bash
kubectl logs -n external-db deployment/external-db-minio | grep http://127.0.0.1
```

Look for a line like: `http://127.0.0.1:33456`

#### Port-forward the MinIO service

```bash
kubectl port-forward -n external-db svc/external-db-minio 9001:9001
```

**Note:** Adjust the port if it differs from the logs.

#### Access the MinIO WebUI

Open your browser and navigate to: `http://localhost:9001`

**Login credentials:**
- Username: `minioadmin`
- Password: `minioadmin`

#### Create S3 buckets

1. In the MinIO UI, create two buckets:
   - `input-data`
   - `output-data`

2. Upload the `users.parquet` file (generated earlier) to the `input-data` bucket

---

## Deploy FastAPI Service

Deploy a simple FastAPI service that provides a sleep endpoint for I/O testing.

### Step 1: Create the namespace

```bash
kubectl create namespace fastapi-sleep
```

### Step 2: Navigate to the FastAPI service directory

```bash
cd external_fastapi_service
```

### Step 3: Build the Docker image

```bash
docker build -t fastapi-sleep .
```

### Step 4: Load the image to Kind

```bash
kind load docker-image fastapi-sleep:latest -n bench-orchestrator
```

### Step 5: Deploy the FastAPI service

```bash
kubectl apply -f fastapi-sleep-deployment.yaml
kubectl apply -f fastapi-sleep-service.yaml
```

### Step 6: Verify the deployment

```bash
kubectl get pods -n fastapi-sleep
kubectl get svc -n fastapi-sleep
```

The service should be accessible at `http://fastapi-sleep.fastapi-sleep.svc.cluster.local:8000`

---

## Next Steps

Your infrastructure is now ready! Proceed to deploy the orchestrators:

**[Orchestrators Setup Guide](ORCHESTRATORS_INSTALLATION.md)** - Deploy Airflow, Argo, Windmill, and Temporal

Or learn about the benchmark scenarios:

**[Benchmark Scenarios Guide](SCENARIOS.md)** - Understand what each scenario tests

---

## Verification Checklist

Before proceeding, ensure:

- [ ] Kind cluster is running (`kubectl get nodes`)
- [ ] Observability stack is deployed (`kubectl get pods -n observ-stack`)
- [ ] Grafana is accessible (`http://localhost:3000`)
- [ ] Grafana dashboards are imported
- [ ] PostgreSQL is running (`kubectl get pods -n external-db`)
- [ ] MinIO S3 is running and buckets are created
- [ ] `users.parquet` is uploaded to `input-data` bucket
- [ ] FastAPI service is deployed (`kubectl get pods -n fastapi-sleep`)

---

## Troubleshooting

If you encounter issues during installation, see the **[Troubleshooting Guide](TROUBLESHOOTING.md)** for common problems and solutions.
