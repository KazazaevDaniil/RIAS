"""
Тесты трансформаций ETL пайплайна (Часть 6: CI/CD)
"""
import pytest
import pandas as pd


def clean_grades(df: pd.DataFrame) -> pd.DataFrame:
    """Silver-трансформация: очистка оценок."""
    df = df.drop_duplicates(subset=["student_id", "subject", "grade_date"])
    df["grade"] = df["grade"].clip(1.0, 5.0)
    return df.dropna(subset=["student_id", "grade"])


def aggregate_gold(df: pd.DataFrame) -> pd.DataFrame:
    """Gold-трансформация: средняя оценка по факультету."""
    return df.groupby("faculty")["grade"].mean().reset_index().rename(columns={"grade": "avg_grade"})


# ── Тесты ─────────────────────────────────────────────────────────────────

def test_clean_grades_removes_duplicates():
    df = pd.DataFrame([
        {"student_id": 1, "subject": "Math", "grade": 4.0, "grade_date": "2024-01-01", "faculty": "ИТ"},
        {"student_id": 1, "subject": "Math", "grade": 4.0, "grade_date": "2024-01-01", "faculty": "ИТ"},
    ])
    result = clean_grades(df)
    assert len(result) == 1


def test_clean_grades_clips_out_of_range():
    df = pd.DataFrame([
        {"student_id": 1, "subject": "Math", "grade": 6.5, "grade_date": "2024-01-01", "faculty": "ИТ"},
        {"student_id": 2, "subject": "Math", "grade": 0.5, "grade_date": "2024-01-01", "faculty": "ИТ"},
    ])
    result = clean_grades(df)
    assert result.iloc[0]["grade"] == 5.0
    assert result.iloc[1]["grade"] == 1.0


def test_clean_grades_drops_nulls():
    df = pd.DataFrame([
        {"student_id": None, "subject": "Math", "grade": 4.0, "grade_date": "2024-01-01", "faculty": "ИТ"},
        {"student_id": 1,    "subject": "Math", "grade": 4.0, "grade_date": "2024-01-02", "faculty": "ИТ"},
    ])
    result = clean_grades(df)
    assert len(result) == 1


def test_aggregate_gold_correct_avg():
    df = pd.DataFrame([
        {"student_id": 1, "subject": "Math", "grade": 4.0, "faculty": "ИТ"},
        {"student_id": 2, "subject": "Math", "grade": 5.0, "faculty": "ИТ"},
        {"student_id": 3, "subject": "Math", "grade": 3.0, "faculty": "Физика"},
    ])
    result = aggregate_gold(df)
    it_avg = result.loc[result["faculty"] == "ИТ", "avg_grade"].values[0]
    assert abs(it_avg - 4.5) < 0.001


def test_aggregate_gold_all_faculties():
    df = pd.DataFrame([
        {"student_id": i, "subject": "X", "grade": 4.0, "faculty": f"Ф{i}"}
        for i in range(5)
    ])
    result = aggregate_gold(df)
    assert len(result) == 5
