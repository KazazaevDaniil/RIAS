"""
Скрипт валидации данных Great Expectations (Часть 2 + Часть 6)
Запускается в CI/CD для проверки качества данных.
"""
import pandas as pd
import sys


def validate_grades_df(df: pd.DataFrame) -> bool:
    errors = []

    # 1. Нет дубликатов по ключу
    dups = df.duplicated(subset=["student_id", "subject", "grade_date"]).sum()
    if dups > 0:
        errors.append(f"❌ Дубликаты: {dups} записей")
    else:
        print("✅ Дубликатов нет")

    # 2. Оценки в диапазоне [1, 5]
    out = df[(df["grade"] < 1.0) | (df["grade"] > 5.0)]
    if not out.empty:
        errors.append(f"❌ Оценки вне диапазона: {len(out)} записей")
    else:
        print("✅ Все оценки в диапазоне [1.0, 5.0]")

    # 3. Нет null в ключевых полях
    nulls = df[["student_id", "grade", "subject"]].isnull().sum().sum()
    if nulls > 0:
        errors.append(f"❌ Null-значения: {nulls}")
    else:
        print("✅ Null-значений в ключевых полях нет")

    # 4. student_id > 0
    invalid_ids = df[df["student_id"] <= 0]
    if not invalid_ids.empty:
        errors.append(f"❌ Невалидные student_id: {len(invalid_ids)}")
    else:
        print("✅ Все student_id валидны")

    if errors:
        print("\n".join(errors))
        return False
    return True


if __name__ == "__main__":
    # Демо-датасет для CI
    sample = pd.DataFrame([
        {"student_id": 1, "subject": "Math", "grade": 4.5, "grade_date": "2024-01-01"},
        {"student_id": 2, "subject": "Math", "grade": 3.8, "grade_date": "2024-01-01"},
        {"student_id": 3, "subject": "Phys", "grade": 5.0, "grade_date": "2024-01-02"},
    ])

    print("=== Great Expectations Validation ===")
    ok = validate_grades_df(sample)
    if ok:
        print("\n✅ Все проверки пройдены!")
        sys.exit(0)
    else:
        print("\n❌ Валидация не прошла!")
        sys.exit(1)
