# 🎓 Университетская Data Platform

Учебная платформа данных на Docker Compose, реализующая все 6 частей задания НИР.

## 📐 Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA SOURCES                                │
│  LMS API (sim)  │  CSV exports  │  Kafka Events (sim)          │
└────────┬────────┴───────┬───────┴──────────┬───────────────────┘
         │                │                  │
         ▼                ▼                  ▼
┌─────────────────┐               ┌──────────────────┐
│   Airflow DAG   │               │  Event Generator │
│  etl_pipeline   │               │  (Python/Kafka)  │
└────────┬────────┘               └────────┬─────────┘
         │                                 │
         ▼                                 ▼
┌────────────────────────────────────────────────────┐
│              MinIO (S3-совместимый)                │
│  bronze/  │  silver/  │  gold/  │  raw/            │
└────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────┐      ┌─────────────────────────────┐
│   ClickHouse   │◄─────│  Airflow DAG kafka_consumer │
│   (аналитика)  │      │  (Kafka → агрегаты)         │
└───────┬────────┘      └─────────────────────────────┘
        │
   ┌────┴────┐
   ▼         ▼
[Grafana] [Cube.js]
              │
              ▼
         [Streamlit]
```

## 🚀 Быстрый старт

### Требования
- Docker Engine ≥ 24
- Docker Compose v2
- RAM ≥ 6 GB
- Disk ≥ 20 GB

### Запуск

```bash
# 1. Клонируйте / распакуйте проект
cd data-platform

# 2. Запустите все сервисы
docker compose up -d

# 3. Дождитесь готовности (~3-5 минут)
docker compose ps

# 4. Откройте интерфейсы
```

### Доступные интерфейсы

| Сервис       | URL                        | Логин / Пароль     |
|--------------|----------------------------|--------------------|
| Airflow      | http://localhost:8080      | admin / admin      |
| MinIO        | http://localhost:9001      | minioadmin / minioadmin |
| Grafana      | http://localhost:3000      | admin / admin      |
| Streamlit    | http://localhost:8501      | —                  |
| Cube.js      | http://localhost:4000      | —                  |
| ClickHouse   | http://localhost:8123      | default / (пусто)  |

## 📦 Структура проекта

```
data-platform/
├── docker-compose.yml          # Все сервисы
├── airflow/
│   └── dags/
│       ├── etl_pipeline.py     # Часть 2: Bronze→Silver→Gold
│       └── kafka_consumer.py   # Часть 4: Kafka→ClickHouse
├── clickhouse/
│   └── init.sql                # Схема БД + тестовые данные
├── grafana/
│   ├── provisioning/           # Авто-настройка datasource
│   └── dashboards/             # JSON дашборды
├── cubejs/
│   └── schema.js               # Часть 5: семантический слой
├── frontend/
│   ├── app.py                  # Часть 5: Streamlit UI
│   └── Dockerfile
├── scripts/
│   ├── event_generator.py      # Часть 4: симулятор Kafka
│   ├── Dockerfile.generator
│   └── run_expectations.py     # Часть 2: валидация данных
├── tests/
│   └── test_transformations.py # Часть 6: pytest
├── .github/
│   └── workflows/ci-cd.yml     # Часть 6: CI/CD
└── docs/
    └── ADR.md                  # Architecture Decision Records
```

## 🔧 Части проекта

### Часть 1 — Доменная архитектура
- Домены: `academic_performance`, `campus_infrastructure`, `student_engagement`
- Инфраструктура: MinIO (S3), Kafka, Airflow — всё в Docker

### Часть 2 — ETL/ELT пайплайн
- DAG `etl_pipeline`: LMS API + CSV → Bronze → Silver → Gold
- Валидация: дубликаты, диапазоны, nulls
- Retry: 3 попытки с задержкой 2 мин

### Часть 3 — Lakehouse
- Bronze / Silver / Gold слои в MinIO
- Трансформации в Python (pandas)
- Feature Store: таблица `student_features` в ClickHouse

### Часть 4 — Real-time
- Event Generator: симулятор → Kafka topic `university-events`
- DAG `kafka_consumer`: Kafka → агрегаты → ClickHouse
- Grafana: реальные дашборды на ClickHouse

### Часть 5 — Semantic Layer
- Cube.js: кубы Students, Grades, RoomOccupancy
- Streamlit: drill-down факультет → группа

### Часть 6 — CI/CD
- GitHub Actions: test → validate → build → deploy
- Pytest: 5 unit-тестов трансформаций

## ❓ Troubleshooting

```bash
# Статус контейнеров
docker compose ps

# Логи конкретного сервиса
docker compose logs airflow-webserver -f

# Перезапустить один сервис
docker compose restart airflow-scheduler

# Полный сброс
docker compose down -v && docker compose up -d
```
