"""Persist generated report artifacts and final status to PostgreSQL."""

from __future__ import annotations

import logging
import os
from typing import Any

import psycopg

logger = logging.getLogger(__name__)


def _connection_string(mask_password: bool = False) -> str:
	"""Build a PostgreSQL connection string from environment variables."""
	required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
	missing = [key for key in required if not os.getenv(key)]
	if missing:
		raise RuntimeError(f"Missing required DB environment variables: {', '.join(missing)}")

	host = os.environ["DB_HOST"]
	port = os.environ["DB_PORT"]
	db_name = os.environ["DB_NAME"]
	user = os.environ["DB_USER"]
	password = os.environ["DB_PASSWORD"]
	if mask_password:
		password = "***"
	return f"host={host} port={port} dbname={db_name} user={user} password={password}"


def save_report_output(job_id: str, report_json: dict[str, Any]) -> None:
	"""Write report JSON and mark report row complete for a job id."""
	if not isinstance(job_id, str) or not job_id:
		raise TypeError("job_id must be a non-empty string")
	if not isinstance(report_json, dict):
		raise TypeError("report_json must be a dict")

	logger.info("Saving report output: job_id=%s report_keys=%s", job_id, sorted(report_json.keys()))
	with psycopg.connect(_connection_string()) as conn:
		with conn.cursor() as cur:
			cur.execute(
				"""
				INSERT INTO reports (job_id, status, stage, report_json, generated_at)
				VALUES (%s, 'completed', 'report_ready', %s::jsonb, NOW())
				ON CONFLICT (job_id)
				DO UPDATE SET
					status = EXCLUDED.status,
					stage = EXCLUDED.stage,
					report_json = EXCLUDED.report_json,
					generated_at = EXCLUDED.generated_at,
					updated_at = NOW();
				""",
				(job_id, psycopg.types.json.Jsonb(report_json)),
			)
	logger.info("Saved report output and marked completed: job_id=%s", job_id)


def store_output_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
	"""Persist report output from payload and return payload with completion status."""
	job_id = payload.get("job_id")
	report_json = payload.get("report_json")
	if not isinstance(job_id, str) or not job_id:
		raise TypeError("'job_id' must be a non-empty string")
	if not isinstance(report_json, dict):
		raise TypeError("'report_json' must be a dict")

	save_report_output(job_id=job_id, report_json=report_json)

	updated_payload = dict(payload)
	updated_payload["status"] = "completed"
	updated_payload["stage"] = "report_ready"
	logger.info("store_output_from_payload finished: job_id=%s status=%s stage=%s", job_id, updated_payload["status"], updated_payload["stage"])
	return updated_payload