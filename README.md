# Orchestrator Benchmark
## AIRFLOW, Argo Workflow, Windmill, Temporal.io
-----------------

## Installation

### Create the Kind cluster

From this root repo folder :

```export DATA_PATH="${PWD}/data"```

envsubst < config_cluster.yaml | kind create cluster --config=-

```envsubst < config_cluster.yaml | kind create cluster --config=-```



### Observability stack

```cd observability-stack```

```helm repo add kube-prometheus-stack https://prometheus-community.github.io/helm-charts```

```helm repo add prometheus-pushgateway https://prometheus-community.github.io/helm-charts```

```helm dependency build```

```helm install observability-stack . -n observ-stack --create-namespace  --values values.yaml```


### Grafana setup


1) Port-forward you grafana pod on port 3000 and connect to it : http://localhost:3000

Initial login : admin / admin . (You have to change the password at the first connexion)

2) Go to your profile on the top-right corner -> Profile ... and generate a Service account with an "admin" token

3) setup a python env (conda, pipenv, what you want...) and ```pip install grafana-backup```

3) ```cd grafana-backup```

4) For any command with grafana-backup, you have to add these env varaible to your current session :


```export GRAFANA_URL=http://localhost:3000```
``` export GRAFANA_TOKEN=your_admin_token here```

5) ```grafana-backup restore _OUTPUT_/*.gz```

This command will import the entire grafana setup and the unique dashboard for viewing the orchestrator metrics for various  experiments.


### Generating a fake parquet data file

Use fake_lake (credits)

```cd fake_data_generation```

```tar -xvf fakelake-x86_64-unknown-linux-musl.tar.gz```

```./fakelake generate users.yaml```

It will generate a 'users.parquet' file inside the same folder.


### Deploying the external databases (Postgres & S3 Minio)

```cd external_databases```

```helm install external-db . -n external-db --create-namespace --values values.yaml```

See the logs of the minio instance and search for the WebUI port like http://127.0.0.1:33456 

Port/forward the WebUI S3 Minio service with this port... and go to it.

Login/password :  minioadmin/minioadmin
And create two buckets 'input-data' and 'output-data'

From the 'input-data' bucket, download by hand the parquet file 'users.parquet'.


### Deploying the external fastAPI micro-service

```kubectl create namespace fastapi-sleep```

```cd external_fastapi_service```

```docker build -t fastapi-sleep .```

```kind load docker-image fastapi-sleep:latest -n bench-orchestrator```

```kubectl apply -f fastapi-sleep-deployment.yaml```

```kubectl apply -f fastapi-sleep-service.yaml```


--------------

### Windmill orchestrator deployment


First, deploy the custom postgresdb for windmill :


```cd orchestrators-helm-deployments/windmill/postgres-custom``

```helm install windmill-postgres . -n windmill --create-namespace --values values.yaml```

#### Benchmark variant 1:

(scenario 1 & 2.a)

Add the official helm chart :

```helm repo add windmill https://windmill-labs.github.io/windmill-helm-charts/```

Prepare the custom python scripts docker image (from the root of this repo project):

```docker build -t windmill-bench-project -f ./docker-orchestrator-factory/windmill-docker-image/Dockerfile .```

Load it to the kind cluster docker registry :

```kind load docker-image windmill-bench-project:latest -n bench-orchestrator```

We have to set 0 for each replica inside the worker group

- deploy the helm chart with these variant values :

```cd orchestrators-helm-deployments/windmill```

```helm install mywindmill windmill/windmill -n windmill --values values_variant_1.yaml```



#### Benchmark variant 2:

(scenario 2.b)

Whe just have to deploy the official windmill helm chart with 4 'defaults' workers (not custom)

```cd orchestrators-helm-deployments/windmill```

```helm install mywindmill windmill/windmill -n windmill --values values_variant_2.yaml```

Or, of course, if you want to deploy the variant 2 from variant 1 :

```helm upgrade mywindmill windmill/windmill -n windmill --values values_variant_2.yaml```


#### Set-up windmill & the benchmark code

portforward the windmill-server... and go to http://localhost:8000

Login : admin@windmill.dev / changeme

Add a first workspace "bench-orchestrator"...
This workspace will be empty for now.

#### 1 - Add the workspace to you local machine

Download the cli...

```wmill workspace add```

? Name this workspace: › bench-orchestrator
? Enter the ID of this workspace (bench-orchestrator) › bench-orchestrator
? Enter the Remote URL (https://app.windmill.dev/) › http://localhost:8000/
? How do you want to login › Browser 

(OR TOKEN method)


#### 2 - Load the windmill scripts & workflows

```cd windmill-code```

```wmill sync push --include-schedules```

You'll retrived all the existing experiments components : scripts, flows, and schedules...
Now refer you to the official documentation to play with all theses components.

Be carefull : perhaps you have to re-write all the env variables set inside each the 6 differents scripts. wmill push seems to ignore it ! Open each yaml files for the 'bash script' and 'python scripts' folders, and copy/paste all the envs to the Settings -> Runtime -> Env section of each script.




--------------


### Airflow orchestrator deployment


```kubectl create namespace airflow```

First, deploy the PV / PVC volume to sync the dags from your local folder to the airflow instance :

Within your current session (path to customize):

```cd orchestrators-helm-deployments/airflow/pvc-claim``

```kubectl apply -f pv_pvc_values.yaml ```


There is two version to compare with Airflow :
- with CeleryExecutor (workers are permanently up)
- with KubernetesExecutor (totally ephemeral workers, one task per up pod)

#### Airflow Benchmark ** CeleryExecutor **


```helm repo add apache-airflow https://airflow.apache.org```


#### variant 1:

(scenario 1, 2.a & 2.b)

Prepare the custom python scripts docker image :

```docker build -t airflow-bench-project -f ./docker-orchestrator-factory/airflow-docker-image/Dockerfile  .```

Load it to the kind cluster docker registry :

```kind load docker-image airflow-bench-project:latest -n bench-orchestrator```


- deploy the helm chart with these variant values :

```cd orchestrators-helm-deployments/airflow```

```helm install airflow3 apache-airflow/airflow -n airflow -values values_celery_variant_1.yaml```



#### First connexion to Airflow 3 WebUI

portforward the airflow-server... and got to http://localhost:8080

Login : admin / admin

Your dags should be already here at your first connexion, according to the volume mapping between : 
local machine <> kind node <> airflow instances (with k8s pv, pvc)
You can manage it directly.



--------------

### Argo Workflow orchestrator deployment


[all the commands should be launched from the folder 'argoworkflow' inside the project]

#### Create the different namespaces :

```kubectl create namespace argo-wf```

#### And the fist namespace entity managed by argo workflow :


```kubectl create namespace team-a```

Yes, we experiment heare a 'multi-tenancy' setup, which is a good poitn for Argo.



#### Deploy argo with Helm

First, define you own pull policy values for all images in argo/pullpolicy_values.yaml
=> (default) IfNotPresent

Download the offcial helm chart:

```helm repo add argo https://argoproj.github.io/argo-helm```

```helm repo update```

And install the realease with the 'multi-tenancy' setup and the 'auth-server=client' mode (for testing):

```cd orchestrators-helm-deployments/argo_workflow ```

```helm install argo-wf argo/argo-workflows --version 0.45.26 -n argo-wf --values values.yaml ```


#### Install the Argo Workflow CLI


Go to : https://github.com/argoproj/argo-workflows/releases/


---


#### RBAC in managed-namespace mode:

#### Argo executor (for each namespace)

For each namespace, like the 'team-a' namespace, an argo executor serviceaccount must to access to all workflow operations...
We will deploy, for each namespace, a custom helm chart to create this serviceaccount and role.

Example with 'team-a' namespace :

```cd argo-wf-values/argo-custom-napespace-setup```

```helm install argo-custom . -n team-a --values values_team_a.yaml```

Test a first workflow launching with this service account :

```argo submit workflow-test/wf-hello-world.yaml --serviceaccount team-a-awf-executor -n team-a --watch```

At the end, we get an error but it does'nt matter.... Check the pod existence and the log with K9s.


#### Argo (humain) Ops (for each namespace)

We also need a 'human' service account to allow the UI connexion, re-submit any pod for testing, etc.
This service account, and the associated role and role-binding object have already been deployed via the custom helm chart.
Test a first workflow launching with this service account :

```argo submit workflow-test/wf-hello-world.yaml --serviceaccount team-a-ops-maintainer -n team-a --watch```


---
#### Test the access with this user ops/maintainer account ('auth-mode=client'):

Get a ephemeral token for this ops/maintainer user's secret :

1) ```ARGO_TOKEN="Bearer $(kubectl get secret team-a-ops-maintainer-secret-token -n team-a -o=jsonpath='{.data.token}' | base64 --decode)"```
```echo $ARGO_TOKEN```

You should see a temporary token.

2) Fill this token on the UI login page

You should be connected now as the team-a ops/maintainer  user...


#### Workflow templates deployment

- Deployment of the argo-workflow-template via a custom helm chart :

```cd argo-wf-values/argo-workflow-template```

```helm install argo-workflow-tasks-template . --values values.yaml```

#### CronWorkflow deployment 
(scenario 1, 2 a )

```cd argo-wf-values/cron-workflow-generation```

```argo cron create ./scenar_2/cron_wf_scenar_2_a_io_bound_4_tasks_11.yaml -n team-a```


-------------------


### Temporal orchestrator deployment

#### Build the workers image

#### Variant 1
(scenario 1, 2 a )


For this variant, all the scripts are : python scripts activities (Temporal need that) that launch sub-process like bash script (equity versus all the others orchestrators) that launch python script inside the workers...

The worker image host the benhcmark python project AND also the temporal code.

From the root of this repo :

```docker build -t temporal-bench-worker -f ./docker-orchestrator-factory/windmill-docker-image/Dockerfile . ----build-arg=/app/temporal-worker/src/run_worker.py```

#### Variant 2
(scenario 2b )


For this variant, all the scripts are : all the activities are purely python activities.

The worker image host the benhcmark python project AND also the temporal code.

From the root of this repo :

```docker build -t temporal-bench-worker -f ./docker-orchestrator-factory/windmill-docker-image/Dockerfile . ----build-arg=/app/temporal-worker/src/run_worker_2.py```


Load it to the kind cluster docker registry :

```kind load docker-image airflow-bench-project:latest -n bench-orchestrator```



#### Deploy the custom postgres database for Temporal

deploiement custom postgres 

```cd orchestrators-helm-deployments/temporal/postgres-custom```

```helm install custom-temporal-postgres-db . -n temporal --create-namespace --values values.yaml```

From inside the database :

```CREATE DATABASE temporal_visibility WITH OWNER=temporal_user;```

helm install --repo https://go.temporal.io/helm-charts --version '>=1.0.0-0' -n temporal -f values.yaml temporal temporal --timeout 900s

#### Generate the PV-PVC claim volume for schedules

```cd orchestrators-helm-deployments/temporal/pvc-claim```

```kubectl apply -f pv_pvc_values.yaml -n temporal```

#### Deploy the temporal workers 


```cd orchestrators-helm-deployments/temporal/worker-deployment```

##### Variant 1
(scenario 1 , 2a)

Workers with bash scripts activities and Workflows MonteCarlo & Workflows IOBound scenar 2a...

```helm install temporal-workers . -n temporal --values vamues_variant_1.yaml```

##### Variant 2
(scenario 2b)

Workers with purely python activities and Workflows scenar 2b...

```helm install temporal-workers . -n temporal --values vamues_variant_1.yaml```


#### Generate the temporal schedules 

With the pvc claim, the pre-defined schedules json definition can be upload to the temporal server wih a Kubernetes job.

```cd orchestrators-helm-deployments/temporal/schedules-jobs-tools```

And choos your scenario, and launch the job according to it...

Example :

```kubectl apply -f create_schedule_scenar_1.yaml -n temporal```

See the job logs...

This will automatically generate the appropriate schedules, visible within the Temporal Web UI.

The schedules are "paused" by default. You just have to "unpause" it to use it.


