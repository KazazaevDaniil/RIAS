@echo off
REM Скрипт запуска для Windows
cd /d %~dp0

echo === Starting Data Platform ===

echo Starting all containers...
docker compose up -d

echo Waiting 40 seconds for PostgreSQL...
timeout /t 40 /nobreak > nul

echo Initializing Airflow...
docker compose run --rm airflow-init

echo Restarting Airflow...
docker compose restart airflow-webserver airflow-scheduler

echo.
echo === Platform is ready! ===
echo   Airflow:    http://localhost:8080  (admin/admin)
echo   MinIO:      http://localhost:9001  (minioadmin/minioadmin)
echo   Grafana:    http://localhost:3000  (admin/admin)
echo   Streamlit:  http://localhost:8501
echo   Cube.js:    http://localhost:4000
echo   ClickHouse: http://localhost:8123/play
echo.
pause
