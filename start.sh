#!/bin/bash
# Скрипт запуска для Linux/Ubuntu
cd "$(dirname "$0")"

echo "=== Starting Data Platform ==="

# Исправить права для Airflow
mkdir -p airflow/logs airflow/dags airflow/plugins
sudo chown -R 50000:0 airflow/logs airflow/dags airflow/plugins 2>/dev/null || \
  chmod -R 777 airflow/logs airflow/dags airflow/plugins

# Запустить все сервисы
docker compose up -d

echo "Waiting for PostgreSQL (30s)..."
sleep 30

# Инициализация Airflow
echo "Initializing Airflow..."
docker compose run --rm airflow-init

# Перезапустить Airflow
docker compose restart airflow-webserver airflow-scheduler

echo ""
echo "=== Platform is ready! ==="
echo "  Airflow:   http://localhost:8080  (admin/admin)"
echo "  MinIO:     http://localhost:9001  (minioadmin/minioadmin)"
echo "  Grafana:   http://localhost:3000  (admin/admin)"
echo "  Streamlit: http://localhost:8501"
echo "  Cube.js:   http://localhost:4000"
echo "  ClickHouse:http://localhost:8123/play (default / пусто)"
