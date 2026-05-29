FROM apache/airflow:2.9.1

USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

USER airflow
RUN pip install --no-cache-dir \
    apache-airflow-providers-amazon \
    boto3 \
    kafka-python \
    pandas \
    pyarrow
