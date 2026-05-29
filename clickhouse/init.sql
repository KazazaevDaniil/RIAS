CREATE DATABASE IF NOT EXISTS university;

CREATE TABLE IF NOT EXISTS university.students (student_id UInt32, name String, faculty String, group_name String, enrolled_year UInt16) ENGINE = MergeTree() ORDER BY student_id;

CREATE TABLE IF NOT EXISTS university.grades (grade_id UInt32, student_id UInt32, subject String, grade Float32, grade_date Date, faculty String, group_name String) ENGINE = MergeTree() ORDER BY (grade_date, student_id);

CREATE TABLE IF NOT EXISTS university.events (event_id String, event_type String, student_id UInt32, room String, campus String, ts DateTime) ENGINE = MergeTree() ORDER BY ts;

CREATE TABLE IF NOT EXISTS university.room_occupancy (window_start DateTime, room String, campus String, count UInt32) ENGINE = MergeTree() ORDER BY (window_start, room);

CREATE TABLE IF NOT EXISTS university.student_features (student_id UInt32, faculty String, group_name String, avg_grade Float32, total_events UInt32, computed_at DateTime DEFAULT now()) ENGINE = ReplacingMergeTree(computed_at) ORDER BY student_id;

INSERT INTO university.students VALUES (1, 'Иван Иванов', 'ИТ', 'ИТ-101', 2022);
INSERT INTO university.students VALUES (2, 'Мария Петрова', 'ИТ', 'ИТ-101', 2022);
INSERT INTO university.students VALUES (3, 'Алексей Сидоров', 'Физика', 'Ф-201', 2021);
INSERT INTO university.students VALUES (4, 'Ольга Козлова', 'Физика', 'Ф-201', 2021);
INSERT INTO university.students VALUES (5, 'Дмитрий Новиков', 'Химия', 'Х-301', 2023);

INSERT INTO university.grades VALUES (1, 1, 'Математика', 4.5, '2024-01-15', 'ИТ', 'ИТ-101');
INSERT INTO university.grades VALUES (2, 1, 'Физика', 3.8, '2024-01-20', 'ИТ', 'ИТ-101');
INSERT INTO university.grades VALUES (3, 2, 'Математика', 5.0, '2024-01-15', 'ИТ', 'ИТ-101');
INSERT INTO university.grades VALUES (4, 2, 'Физика', 4.2, '2024-01-20', 'ИТ', 'ИТ-101');
INSERT INTO university.grades VALUES (5, 3, 'Математика', 3.5, '2024-01-15', 'Физика', 'Ф-201');
INSERT INTO university.grades VALUES (6, 3, 'Химия', 4.0, '2024-01-22', 'Физика', 'Ф-201');
INSERT INTO university.grades VALUES (7, 4, 'Математика', 4.8, '2024-01-15', 'Физика', 'Ф-201');
INSERT INTO university.grades VALUES (8, 5, 'Органика', 3.2, '2024-01-18', 'Химия', 'Х-301');

INSERT INTO university.student_features VALUES (1, 'ИТ', 'ИТ-101', 4.15, 10, now());
INSERT INTO university.student_features VALUES (2, 'ИТ', 'ИТ-101', 4.60, 15, now());
INSERT INTO university.student_features VALUES (3, 'Физика', 'Ф-201', 3.75, 8, now());
INSERT INTO university.student_features VALUES (4, 'Физика', 'Ф-201', 4.80, 12, now());
INSERT INTO university.student_features VALUES (5, 'Химия', 'Х-301', 3.20, 5, now());
