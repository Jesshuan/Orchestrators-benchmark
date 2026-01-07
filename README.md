

### Creating the Kind cluster

```kind create cluster --config config_cluster.yml```



### Observability stack

```cd observability-stack```

```helm repo add kube-prometheus-stack https://prometheus-community.github.io/helm-charts```

```helm repo add prometheus-pushgateway https://prometheus-community.github.io/helm-charts```

```helm dependency build```

```helm install observability-stack . -n observ-stack --create-namespace  --values values.yaml```


### Grafana setup


1) Port-forward you grafana pod on port 3000 and connect to it : http://localhost:3000

2) Go to your profile on the top-right corner -> Profile ... and generate a Service account with an "admin" token

3) setup a python env (conda, pipenv, what you want...) and ```pip install grafana-backup```

3) ```cd grafana-backup```

4) For any command with grafana-backup, you have to add these env varaible to your current session :


```export GRAFANA_URL=http://localhost:3000```
``` export GRAFANA_TOKEN=[...your_admin_token...]```

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

Port/forward the WebUI S3 Minio service (with k9s or ```kubectl apply port-forward .... ```),

go to localhost:33275

(see the los of the pod if needed to choose the right port)

Login/password :  minioadmin/minioadmin
And create two buckets 'input_data' and 'output_data'

From the 'input_data' bucket, download by hand the parquet file 'users.parquet'.


### Deploying the external fastAPI micro-service

```kubectl create namespace fastapi-sleep```

```cd external_fastapi_service```

```docker build -t fastapi-sleep .```

```kind load docker-image fastapi-sleep:latest -n bench-orchestrator```

```kubectl apply -f fastapi-sleep-deployment.yaml```

```kubectl apply -f fastapi-sleep-service.yaml```




### Windmill orchestrator deployment


First, deploy the custom postgresdb for windmill :


```cd orchestrators-helm-deployments/windmill/postgres-custom``

```helm install windmill-postgres . -n windmill --create-namespace --values values.yaml```






#### Benchmark variant 1:

(scenario 1 & 2.a)



Prepare the custom python scripts docker image :

```docker build -t windmill-bench-project -f ./docker-orchestrator-factory/windmill-docker-image/Dockerfile .```

Load it to the kind cluster docker registry :

```kind load docker-image windmill-bench-project:latest -n bench-orchestrator```

We have to set 0 for each replica inside the worker group

- deploy the helm chart with these variant values :

```cd orchestrators-helm-deployments/windmill```

```helm install mywindmill windmill/windmill -n windmill --values values_variant_1.yaml```

- and the custom worker additionnal chart values for deploying the 4 custom python deps additionnals workers 

```helm install windmill-custom-worker windmill/windmill -n windmill --values values_custom_worker.yaml```


#### Benchmark variant 2:

(scenario 2.b)

Whe just have to deploy the official windmill helm chart with 4 'defaults' workers

```cd orchestrators-helm-deployments/windmill```

```helm install mywindmill windmill/windmill -n windmill --values values_variant_2.yaml```



### First connexion to Windmill

Login : ... / changeme

Add a first workspace "bench-orchestrator"


### - Load the windmill scripts & workflows


#### 1 - Add the workspace to you local machine

Download the cli...

```wmill workspace add```

? Name this workspace: › bench-orchestrator
? Enter the ID of this workspace (bench-orchestrator) › bench-orchestrator
? Enter the Remote URL (https://app.windmill.dev/) › http://localhost:8000/
? How do you want to login › Browser 

(OR TOKEN method)



