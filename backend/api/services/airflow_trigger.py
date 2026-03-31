"""Service helper for triggering the Airflow DAG."""

import base64
import json
import logging
import os
from urllib import error, request
# accepts the job_id
# make a http post to the Airflow API endpoint to trigger the DAG with the job_id in the conf
# send the {"conf": {"job_id": "<job_id>"}} as the payload to the Airflow API endpoint to trigger the DAG
# Airflow API endpoint for triggering a DAG: POST /api/v1/dags/{dag_id}/dagRuns
# example: POST /api/v1/dags/revue_processing_pipeline/dagRuns with payload {"conf": {"job_id": "revue-abc123"}} to trigger the DAG for job_id "revue-abc123"  
#use basic auth for the airflow creds
# return the response from the Airflow API call, which includes the DAG run ID and status, back to the caller of this service for tracking purposes

logger = logging.getLogger(__name__)

def trigger_airflow_dag(job_id: str) -> str:
    """Trigger the Airflow DAG for the given job_id and return the dag run id."""

    airflow_url = os.getenv("AIRFLOW_URL", "http://localhost:8080")
    airflow_username = os.getenv("AIRFLOW_USERNAME", "airflow")
    airflow_password = os.getenv("AIRFLOW_PASSWORD", "airflow")

    endpoint = f"{airflow_url}/api/v1/dags/revue_processing_pipeline/dagRuns"       # revue_processing_pipeline is the dag_id defined in the Airflow DAG file (revue_pipeline.py)
    payload = {"conf": {"job_id": job_id}}
    logger.info("Triggering Airflow DAG: endpoint=%s job_id=%s username=%s", endpoint, job_id, airflow_username)

    auth_token = base64.b64encode(f"{airflow_username}:{airflow_password}".encode("utf-8")).decode("utf-8")
    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth_token}",
        },
        method="POST",
    )

    try:
        with request.urlopen(req) as resp:
            status_code = resp.getcode()
            body = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        logger.error("Airflow trigger HTTP error: endpoint=%s job_id=%s status=%s body=%s", endpoint, job_id, exc.code, body)
        raise RuntimeError(f"Failed to trigger Airflow DAG: {body}") from exc
    except error.URLError as exc:
        logger.error("Airflow trigger URL error: endpoint=%s job_id=%s reason=%s", endpoint, job_id, exc.reason)
        raise RuntimeError(f"Unable to reach Airflow at {endpoint}: {exc.reason}") from exc

    if status_code not in (200, 201):
        logger.error("Airflow trigger unexpected status: endpoint=%s job_id=%s status=%s body=%s", endpoint, job_id, status_code, body)
        raise RuntimeError(f"Failed to trigger Airflow DAG: {body}")

    parsed = json.loads(body)
    dag_run_id = str(parsed.get("dag_run_id", ""))
    logger.info("Airflow trigger accepted: job_id=%s dag_run_id=%s status=%s", job_id, dag_run_id, status_code)
    return dag_run_id