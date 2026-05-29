"""
Симулятор событий университета → Kafka
Часть 4: генерирует события "студент вошёл в аудиторию", "отправил задание" и т.д.
"""

import json
import random
import time
import uuid
from datetime import datetime

from kafka import KafkaProducer
import os

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC = "university-events"

EVENT_TYPES = [
    "student_entered_room",
    "student_left_room",
    "assignment_submitted",
    "lecture_started",
    "lecture_ended",
]

ROOMS = ["А101", "А102", "Б201", "Б202", "В301", "Библиотека"]
CAMPUSES = ["Главный", "Северный", "Южный"]


def make_event():
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": random.choice(EVENT_TYPES),
        "student_id": random.randint(1, 100),
        "room": random.choice(ROOMS),
        "campus": random.choice(CAMPUSES),
        "ts": datetime.utcnow().isoformat(),
    }


def main():
    print(f"Connecting to Kafka at {KAFKA_SERVERS}...")
    # Ждём Kafka
    for attempt in range(30):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            print("✅ Connected to Kafka!")
            break
        except Exception as e:
            print(f"Attempt {attempt + 1}/30 failed: {e}")
            time.sleep(5)
    else:
        print("❌ Could not connect to Kafka. Exiting.")
        return

    print(f"Publishing events to topic '{TOPIC}'...")
    count = 0
    while True:
        event = make_event()
        producer.send(TOPIC, value=event)
        count += 1
        if count % 10 == 0:
            producer.flush()
            print(f"Sent {count} events. Last: {event['event_type']} → {event['room']}")
        time.sleep(random.uniform(0.5, 2.0))


if __name__ == "__main__":
    main()
