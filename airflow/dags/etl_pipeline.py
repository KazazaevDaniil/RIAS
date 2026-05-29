"""
DAG: etl_to_raw_layer
Часть 2: Загрузка данных из источников в Raw-слой (MinIO/S3) в формате Parquet
с валидацией Great Expectations и retry-логикой.
"""

from __future__ import annotations

import io
import json
import logging
import random
from datetime import datetime, timedelta

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from airflow import DAG
from airflow.operators.python import PythonOperator

log = logging.getLogger(__name__)

# ── Настройки MinIO ────────────────────────────────────────────────────────
MINIO_ENDPOINT = "http://minio:9000"
AWS_KEY = "minioadmin"
AWS_SECRET = "minioadmin"


def get_s3_client():
    import boto3
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=AWS_KEY,
        aws_secret_access_key=AWS_SECRET,
    )


# ── 1. Симуляция API LMS ───────────────────────────────────────────────────
def fetch_lms_data(**ctx):
    log.info("Fetching data from LMS API (simulation)...")
    records = []
    faculties = ["ИТ", "Физика", "Химия"]
    subjects = ["Математика", "Физика", "Химия", "Алгоритмы", "БД"]
    for i in range(1, 51):
        records.append({
            "student_id": i,
            "subject": random.choice(subjects),
            "grade": round(random.uniform(2.5, 5.0), 2),
            "faculty": random.choice(faculties),
            "group_name": f"Г-{random.randint(100, 305)}",
            "grade_date": (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d"),
        })
    df = pd.DataFrame(records)
    log.info(f"Fetched {len(df)} LMS records")

    # Сохранить в XCom (упрощённо — JSON)
    ctx["ti"].xcom_push(key="lms_df", value=df.to_json())


# ── 2. Симуляция CSV-выгрузки ──────────────────────────────────────────────
def fetch_csv_data(**ctx):
    log.info("Fetching student roster CSV (simulation)...")
    students = []
    for i in range(1, 51):
        students.append({
            "student_id": i,
            "name": f"Student_{i}",
            "faculty": random.choice(["ИТ", "Физика", "Химия"]),
            "group_name": f"Г-{random.randint(100, 305)}",
            "enrolled_year": random.choice([2021, 2022, 2023]),
        })
    df = pd.DataFrame(students)
    ctx["ti"].xcom_push(key="csv_df", value=df.to_json())
    log.info(f"Fetched {len(df)} student records from CSV")


# ── 3. Валидация данных (Great Expectations-style) ─────────────────────────
def validate_data(**ctx):
    lms_json = ctx["ti"].xcom_pull(key="lms_df", task_ids="fetch_lms_data")
    df = pd.read_json(lms_json)

    errors = []

    # Проверка дубликатов по student_id + subject + grade_date
    dups = df.duplicated(subset=["student_id", "subject", "grade_date"]).sum()
    if dups > 0:
        errors.append(f"Found {dups} duplicate records")

    # Проверка диапазона оценок
    out_of_range = df[(df["grade"] < 1.0) | (df["grade"] > 5.0)]
    if not out_of_range.empty:
        errors.append(f"{len(out_of_range)} grades out of [1.0, 5.0] range")

    # Проверка nulls
    nulls = df.isnull().sum().sum()
    if nulls > 0:
        errors.append(f"Found {nulls} null values")

    if errors:
        log.warning(f"Validation warnings: {errors}")
    else:
        log.info("✅ Validation passed: no errors")

    ctx["ti"].xcom_push(key="validation_ok", value=len(errors) == 0)


# ── 4. Загрузка в S3 (MinIO) в Parquet ────────────────────────────────────
def upload_to_raw(**ctx):
    lms_json = ctx["ti"].xcom_pull(key="lms_df", task_ids="fetch_lms_data")
    csv_json = ctx["ti"].xcom_pull(key="csv_df", task_ids="fetch_csv_data")

    s3 = get_s3_client()
    run_date = ctx["ds"]  # YYYY-MM-DD

    for name, raw_json, bucket in [
        ("grades", lms_json, "bronze"),
        ("students", csv_json, "bronze"),
    ]:
        df = pd.read_json(raw_json)
        table = pa.Table.from_pandas(df)
        buf = io.BytesIO()
        pq.write_table(table, buf)
        buf.seek(0)

        key = f"university/{name}/date={run_date}/{name}.parquet"
        s3.put_object(Bucket=bucket, Key=key, Body=buf.read())
        log.info(f"✅ Uploaded {name} → s3://bronze/{key}")


# ── 5. Silver: очистка данных ──────────────────────────────────────────────
def transform_to_silver(**ctx):
    s3 = get_s3_client()
    run_date = ctx["ds"]

    obj = s3.get_object(Bucket="bronze", Key=f"university/grades/date={run_date}/grades.parquet")
    df = pd.read_parquet(io.BytesIO(obj["Body"].read()))

    # Очистка: убрать дубликаты, заполнить пропуски
    df = df.drop_duplicates(subset=["student_id", "subject", "grade_date"])
    df["grade"] = df["grade"].clip(1.0, 5.0)

    table = pa.Table.from_pandas(df)
    buf = io.BytesIO()
    pq.write_table(table, buf)
    buf.seek(0)

    key = f"university/grades/date={run_date}/grades_clean.parquet"
    s3.put_object(Bucket="silver", Key=key, Body=buf.read())
    log.info(f"✅ Silver layer ready: s3://silver/{key}")


# ── 6. Gold: агрегаты + запись в ClickHouse ───────────────────────────────
def transform_to_gold(**ctx):
    import urllib.request
    s3 = get_s3_client()
    run_date = ctx["ds"]

    obj = s3.get_object(Bucket="silver", Key=f"university/grades/date={run_date}/grades_clean.parquet")
    df = pd.read_parquet(io.BytesIO(obj["Body"].read()))

    # Агрегат: средняя оценка по факультету и группе
    agg = df.groupby(["faculty", "group_name"])["grade"].mean().reset_index()
    agg.columns = ["faculty", "group_name", "avg_grade"]
    agg["computed_date"] = run_date

    table = pa.Table.from_pandas(agg)
    buf = io.BytesIO()
    pq.write_table(table, buf)
    buf.seek(0)

    key = f"university/avg_grades/date={run_date}/avg_grades.parquet"
    s3.put_object(Bucket="gold", Key=key, Body=buf.read())
    log.info(f"✅ Gold layer ready: s3://gold/{key}")

    # Вставка в ClickHouse через HTTP API
    ch_url = "http://clickhouse:8123/?query=INSERT+INTO+university.student_features+FORMAT+JSONEachRow"
    for _, row in df.groupby("student_id")["grade"].mean().reset_index().iterrows():
        payload = json.dumps({
            "student_id": int(row["student_id"]),
            "faculty": "unknown",
            "group_name": "unknown",
            "avg_grade": float(row["grade"]),
            "total_events": 0,
        }) + "\n"
        req = urllib.request.Request(ch_url, data=payload.encode(), method="POST")
        urllib.request.urlopen(req)

    log.info("✅ Gold features written to ClickHouse")


# ── DAG Definition ─────────────────────────────────────────────────────────
default_args = {
    "owner": "airflow",
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
    "email_on_failure": False,
}

with DAG(
    dag_id="etl_to_raw_layer",
    default_args=default_args,
    description="ETL: LMS + CSV → Bronze → Silver → Gold (MinIO/Parquet)",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["etl", "university", "bronze", "silver", "gold"],
) as dag:

    t1 = PythonOperator(task_id="fetch_lms_data",    python_callable=fetch_lms_data)
    t2 = PythonOperator(task_id="fetch_csv_data",    python_callable=fetch_csv_data)
    t3 = PythonOperator(task_id="validate_data",     python_callable=validate_data)
    t4 = PythonOperator(task_id="upload_to_raw",     python_callable=upload_to_raw)
    t5 = PythonOperator(task_id="transform_to_silver", python_callable=transform_to_silver)
    t6 = PythonOperator(task_id="transform_to_gold",   python_callable=transform_to_gold)

    [t1, t2] >> t3 >> t4 >> t5 >> t6
