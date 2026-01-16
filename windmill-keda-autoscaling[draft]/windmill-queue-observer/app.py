from fastapi import FastAPI, HTTPException, Response
import httpx
import os
from datetime import datetime, timezone
from prometheus_client import CollectorRegistry, Gauge, generate_latest, CONTENT_TYPE_LATEST

WINDMILL_URL = os.getenv("WINDMILL_URL")  # e.g. https://team-a.windmill.example.com
WINDMILL_TOKEN = os.getenv("WINDMILL_TOKEN")

WORKSPACES = [{"workspace": "dev", "tag": "project-a"},
              {"workspace": "prod", "tag": "project-a"}]

app = FastAPI()

registry = CollectorRegistry()
pending_jobs_gauge = Gauge('pending_jobs', 'Number of jobs waiting in queue', ['tag'], registry=registry)

@app.get("/metrics")
async def metrics():
    """
    Returns the number of pending jobs for a given workspace,
    optionally filtered by 'tag'.
    Example:
      /pending_jobs/dev?tag=project-a
    """

    for w_dict in WORKSPACES:
        workspace = w_dict.get("workspace")
        tag = w_dict.get("tag")

        headers = {"Authorization": f"Bearer {WINDMILL_TOKEN}"}

        if tag:
            url = f"{WINDMILL_URL}/api/w/{workspace}/jobs/queue/list?tag={tag}"
        else:
            url = f"{WINDMILL_URL}/api/w/{workspace}/jobs/queue/list"

        async with httpx.AsyncClient() as client:
            try:
                r = await client.get(url, headers=headers)
                r.raise_for_status()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error fetching jobs: {e}")

        jobs_list = r.json()

        #jobs_scheduled_date = [datetime.strptime(j.get("scheduled_for"), "%Y-%m-%dT%H:%M:%S") for j in jobs_list if j.get("schedule_path") is not None and not j.get("running")]
        jobs_scheduled_date = [j.get("scheduled_for") for j in jobs_list if j.get("schedule_path") is not None and not j.get("running")]
        jobs_sch_dt = [datetime.fromisoformat(ts.replace("Z", "+00:00")) for ts in jobs_scheduled_date]
        nb_jobs_sch_pending = len([ts for ts in jobs_sch_dt if ts < datetime.now(timezone.utc)])
        nb_jobs_not_scheduled_queued = len([j for j in jobs_list if j.get("schedule_path") is None and not j.get("running")])

        nb_jobs = nb_jobs_sch_pending  + nb_jobs_not_scheduled_queued

        if tag:
            metric_tag = workspace + "_" + tag
        else:
            metric_tag = workspace + "_all"

        pending_jobs_gauge.labels(tag=metric_tag).set(nb_jobs)

    return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)