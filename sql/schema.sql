-- TrainHub: четыре сущности; даты хранятся в формате ISO YYYY-MM-DD.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    position TEXT NOT NULL DEFAULT 'Сотрудник',
    role TEXT NOT NULL DEFAULT 'сотрудник'
);

CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    duration_days INTEGER NOT NULL CHECK (duration_days > 0),
    course_type TEXT NOT NULL DEFAULT 'онлайн',
    is_mandatory INTEGER NOT NULL DEFAULT 0 CHECK (is_mandatory IN (0, 1))
);

CREATE TABLE IF NOT EXISTS trainings (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    course_id INTEGER NOT NULL REFERENCES courses(id),
    enrollment_date TEXT NOT NULL CHECK (
        length(enrollment_date) = 10
        AND date(enrollment_date, '+0 days') IS NOT NULL
        AND date(enrollment_date, '+0 days') = enrollment_date
    ),
    is_cancelled INTEGER NOT NULL DEFAULT 0 CHECK (is_cancelled IN (0, 1)),
    is_completed INTEGER NOT NULL DEFAULT 0 CHECK (is_completed IN (0, 1))
);

-- Повторное неотмененное назначение на ту же дату запрещено и в БД.
CREATE UNIQUE INDEX IF NOT EXISTS unique_training_assignment
ON trainings(employee_id, course_id, enrollment_date)
WHERE is_cancelled = 0;
CREATE INDEX IF NOT EXISTS trainings_course ON trainings(course_id);

CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY,
    training_id INTEGER NOT NULL REFERENCES trainings(id),
    score INTEGER NOT NULL CHECK (
        typeof(score) = 'integer' AND score BETWEEN 0 AND 100
    ),
    completed_date TEXT NOT NULL CHECK (
        length(completed_date) = 10
        AND date(completed_date, '+0 days') IS NOT NULL
        AND date(completed_date, '+0 days') = completed_date
    ),
    comment TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS results_training ON results(training_id);

-- Правила существующего Result проверяются также при прямом SQL-вводе.
CREATE TRIGGER IF NOT EXISTS validate_result_insert
BEFORE INSERT ON results
WHEN NOT EXISTS (
    SELECT 1 FROM trainings
    WHERE id = NEW.training_id AND is_completed = 1 AND is_cancelled = 0
      AND enrollment_date <= NEW.completed_date
)
BEGIN
    SELECT RAISE(ABORT, 'Result requires completed training and valid date');
END;

CREATE TRIGGER IF NOT EXISTS validate_result_update
BEFORE UPDATE ON results
WHEN NOT EXISTS (
    SELECT 1 FROM trainings
    WHERE id = NEW.training_id AND is_completed = 1 AND is_cancelled = 0
      AND enrollment_date <= NEW.completed_date
)
BEGIN
    SELECT RAISE(ABORT, 'Result requires completed training and valid date');
END;
