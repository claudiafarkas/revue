# Airflow worker image for the Revue.ai pipeline.
FROM apache/airflow:2.9.1-python3.12

# Copy DAGs and task modules into the image.
COPY dags/ /opt/airflow/dags/
COPY tasks/ /opt/airflow/tasks/

# Make tasks/ importable as a top-level package from DAG code.
ENV PYTHONPATH="/opt/airflow/tasks:${PYTHONPATH}"

# Install Python dependencies for Airflow tasks.
COPY requirements.txt /tmp/airflow-requirements.txt
RUN pip install --no-cache-dir -r /tmp/airflow-requirements.txt