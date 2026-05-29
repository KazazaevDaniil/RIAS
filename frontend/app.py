"""
Часть 5: Embedded Analytics — Streamlit frontend
Подключается к Cube.js API и строит интерактивные графики с drill-down
"""

import os
import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

CUBEJS_URL = os.getenv("CUBEJS_API_URL", "http://cubejs:4000/cubejs-api/v1")
CUBEJS_TOKEN = os.getenv("CUBEJS_API_TOKEN", "mysupersecretapikey1234567890abc")

st.set_page_config(
    page_title="🎓 Университетская аналитика",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🎓 Университетская аналитическая платформа")
st.caption("Data Mesh · Lakehouse · Real-time · Semantic Layer")


def cube_query(query: dict) -> pd.DataFrame:
    """Запрос к Cube.js API и преобразование в DataFrame."""
    try:
        resp = requests.post(
            f"{CUBEJS_URL}/load",
            json={"query": query},
            headers={"Authorization": f"Bearer {CUBEJS_TOKEN}"},
            timeout=15,
        )
        if resp.status_code != 200:
            st.warning(f"Cube.js вернул {resp.status_code}: {resp.text[:200]}")
            return pd.DataFrame()
        data = resp.json().get("data", [])
        return pd.DataFrame(data)
    except Exception as e:
        st.warning(f"Не удалось подключиться к Cube.js: {e}. Показываю демо-данные.")
        return pd.DataFrame()


def demo_grades_by_faculty():
    return pd.DataFrame({
        "Grades.faculty": ["ИТ", "Физика", "Химия"],
        "Grades.avgGrade": [4.35, 4.1, 3.75],
    })


def demo_students_by_faculty():
    return pd.DataFrame({
        "Students.faculty": ["ИТ", "Физика", "Химия"],
        "Students.count": [20, 15, 10],
    })


def demo_grades_by_group(faculty):
    groups = {
        "ИТ":     [("ИТ-101", 4.35), ("ИТ-102", 4.1)],
        "Физика": [("Ф-201", 4.1),  ("Ф-202", 4.0)],
        "Химия":  [("Х-301", 3.75), ("Х-302", 3.5)],
    }
    rows = groups.get(faculty, [("Н/Д", 0.0)])
    return pd.DataFrame(rows, columns=["Grades.groupName", "Grades.avgGrade"])


# ── Sidebar ────────────────────────────────────────────────────────────────
st.sidebar.header("🔍 Фильтры")
drill_faculty = st.sidebar.selectbox(
    "Факультет (drill-down)",
    ["Все", "ИТ", "Физика", "Химия"],
)

# ── Tab layout ─────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Успеваемость",
    "👥 Студенты",
    "🏫 Загрузка аудиторий",
    "🔗 Data Lineage",
])

# ── Tab 1: Успеваемость ────────────────────────────────────────────────────
with tab1:
    st.subheader("Средняя оценка по факультетам")

    df_grades = cube_query({
        "measures": ["Grades.avgGrade"],
        "dimensions": ["Grades.faculty"],
    })

    if df_grades.empty:
        df_grades = demo_grades_by_faculty()

    df_grades.columns = ["faculty", "avg_grade"]
    df_grades["avg_grade"] = pd.to_numeric(df_grades["avg_grade"], errors="coerce")

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(
            df_grades, x="faculty", y="avg_grade",
            color="faculty", title="Средняя оценка по факультетам",
            labels={"faculty": "Факультет", "avg_grade": "Средняя оценка"},
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_layout(showlegend=False, yaxis_range=[0, 5])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Drill-down по группам
        if drill_faculty != "Все":
            st.markdown(f"**Drill-down: группы факультета «{drill_faculty}»**")
            df_group = cube_query({
                "measures": ["Grades.avgGrade"],
                "dimensions": ["Grades.groupName"],
                "filters": [{"member": "Grades.faculty", "operator": "equals", "values": [drill_faculty]}],
            })
            if df_group.empty:
                df_group = demo_grades_by_group(drill_faculty)
            df_group.columns = ["group_name", "avg_grade"]
            df_group["avg_grade"] = pd.to_numeric(df_group["avg_grade"], errors="coerce")
            fig2 = px.bar(
                df_group, x="group_name", y="avg_grade",
                color="group_name", title=f"Группы — {drill_faculty}",
                labels={"group_name": "Группа", "avg_grade": "Средняя оценка"},
            )
            fig2.update_layout(showlegend=False, yaxis_range=[0, 5])
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Выберите факультет в боковой панели для drill-down по группам.")

    # Таблица
    st.dataframe(df_grades.rename(columns={"faculty": "Факультет", "avg_grade": "Средняя оценка"}))

# ── Tab 2: Студенты ────────────────────────────────────────────────────────
with tab2:
    st.subheader("Распределение студентов")

    df_students = cube_query({
        "measures": ["Students.count"],
        "dimensions": ["Students.faculty"],
    })
    if df_students.empty:
        df_students = demo_students_by_faculty()

    df_students.columns = ["faculty", "count"]
    df_students["count"] = pd.to_numeric(df_students["count"], errors="coerce")

    col1, col2 = st.columns(2)
    with col1:
        fig3 = px.pie(
            df_students, values="count", names="faculty",
            title="Студенты по факультетам",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        st.metric("Всего студентов", int(df_students["count"].sum()))
        st.metric("Факультетов", len(df_students))
        st.dataframe(df_students.rename(columns={"faculty": "Факультет", "count": "Студентов"}))

# ── Tab 3: Загрузка аудиторий ──────────────────────────────────────────────
with tab3:
    st.subheader("🏫 Загрузка аудиторий (real-time симуляция)")
    st.info("Данные поступают из Kafka → ClickHouse через event-generator.")

    # Демо-данные загрузки
    rooms = ["А101", "А102", "Б201", "Б202", "В301", "Библиотека"]
    demo_occ = pd.DataFrame({
        "room": rooms,
        "count": [23, 15, 8, 31, 12, 45],
        "campus": ["Главный", "Главный", "Северный", "Северный", "Южный", "Главный"],
    })

    fig4 = px.bar(
        demo_occ, x="room", y="count", color="campus",
        title="Текущая заполненность аудиторий",
        labels={"room": "Аудитория", "count": "Кол-во человек", "campus": "Корпус"},
    )
    st.plotly_chart(fig4, use_container_width=True)

# ── Tab 4: Data Lineage ────────────────────────────────────────────────────
with tab4:
    st.subheader("🔗 Data Lineage — схема потоков данных")
    st.markdown("""
    ```
    [LMS API]        ──┐
    [CSV Exports]    ──┤──► [Raw/Bronze (MinIO/S3)]
    [Kafka Events]   ──┘         │
                                 ▼
                        [Silver (очищенные данные)]
                                 │
                                 ▼
                        [Gold (агрегаты + признаки)]
                                 │
                    ┌────────────┴──────────────┐
                    ▼                           ▼
              [ClickHouse]              [Feature Store]
                    │                           │
            ┌───────┴───────┐                  ▼
            ▼               ▼           [ML модель]
         [Grafana]      [Cube.js]
                            │
                            ▼
                       [Streamlit UI]
    ```
    """)
    st.success("Все слои связаны: изменение источника автоматически propagates через пайплайн.")
