"""
DAG: kafka_to_clickhouse
Часть 4: Чтение событий из Kafka и запись в ClickHouse.
"""

from __future__ import annotations
import json
import logging
import urllib.request
from datetime import datetime, timedelta
from collections import defaultdict

from airflow import DAG
from airflow.operators.python import PythonOperator

log = logging.getLogger(__name__)


def consume_and_aggregate(**ctx):
    from kafka import KafkaConsumer

    consumer = KafkaConsumer(
        "university-events",
        bootstrap_servers="kafka:9092",
        auto_offset_reset="earliest",   # читать с начала если нет offset
        consumer_timeout_ms=15000,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        group_id=f"airflow-aggregator-{ctx['ts_nodash']}",  # уникальная группа каждый раз
    )

    room_counts = defaultdict(lambda: defaultdict(int))
    total = 0

    for msg in consumer:
        event = msg.value
        room = event.get("room", "unknown")
        campus = event.get("campus", "unknown")
        if event.get("event_type") == "student_entered_room":
            room_counts[campus][room] += 1
        total += 1

    consumer.close()
    log.info(f"Consumed {total} events")

    if not room_counts:
        log.info("No events yet — inserting demo data")
        room_counts["Главный"]["А101"] = 5
        room_counts["Главный"]["А102"] = 3
        room_counts["Северный"]["Б201"] = 8

    window_start = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    ch_url = "http://clickhouse:8123/?query=INSERT+INTO+university.room_occupancy+FORMAT+JSONEachRow"

    for campus, rooms in room_counts.items():
        for room, count in rooms.items():
            payload = json.dumps({
                "window_start": window_start,
                "room": room,
                "campus": campus,
                "count": count,
            }) + "\n"
            req = urllib.request.Request(ch_url, data=payload.encode(), method="POST")
            urllib.request.urlopen(req)

    log.info(f"Written {sum(len(r) for r in room_counts.values())} room aggregates to ClickHouse")


def write_events_sample(**ctx):
    from kafka import KafkaConsumer

    consumer = KafkaConsumer(
        "university-events",
        bootstrap_servers="kafka:9092",
        auto_offset_reset="earliest",
        consumer_timeout_ms=15000,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        group_id=f"airflow-events-writer-{ctx['ts_nodash']}",  # уникальная группа
    )

    ch_url = "http://clickhouse:8123/?query=INSERT+INTO+university.events+FORMAT+JSONEachRow"
    batch = []

    for msg in consumer:
        e = msg.value
        ts = e.get("ts", "")[:19].replace("T", " ")
        if len(ts) < 19:
            ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        batch.append(json.dumps({
            "event_id":   e.get("event_id", ""),
            "event_type": e.get("event_type", ""),
            "student_id": int(e.get("student_id", 0)),
            "room":       e.get("room", ""),
            "campus":     e.get("campus", ""),
            "ts":         ts,
        }))

    consumer.close()

    if not batch:
        log.info("No Kafka events — inserting demo events")
        import uuid, random
        rooms = ["А101", "А102", "Б201", "В301"]
        campuses = ["Главный", "Северный"]
        types = ["student_entered_room", "assignment_submitted", "lecture_started"]
        for i in range(10):
            batch.append(json.dumps({
                "event_id":   str(uuid.uuid4()),
                "event_type": random.choice(types),
                "student_id": random.randint(1, 5),
                "room":       random.choice(rooms),
                "campus":     random.choice(campuses),
                "ts":         datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            }))

    payload = "\n".join(batch) + "\n"
    req = urllib.request.Request(ch_url, data=payload.encode(), method="POST")
    urllib.request.urlopen(req)
    log.info(f"Written {len(batch)} events to ClickHouse")


default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
    "email_on_failure": False,
}

with DAG(
    dag_id="kafka_to_clickhouse",
    default_args=default_args,
    description="Kafka → ClickHouse: агрегаты загрузки аудиторий",
    schedule="*/5 * * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["streaming", "kafka", "clickhouse"],
) as dag:

    t1 = PythonOperator(task_id="consume_and_aggregate", python_callable=consume_and_aggregate)
    t2 = PythonOperator(task_id="write_events_sample",   python_callable=write_events_sample)

    t1 >> t2
