-- Единственный источник SELECT-запросов для Python и демонстрации в CLI.
-- Параметры ? передаются через sqlite3; в CLI их задают через .parameter.

-- name: employees
-- 01. SELECT: реестр сотрудников.
SELECT id, name, email, position, role
FROM employees ORDER BY name, id;

-- name: courses
-- 02. SELECT: каталог курсов.
SELECT id, name, description, duration_days, course_type, is_mandatory
FROM courses ORDER BY id;

-- name: mandatory_courses
-- 03. WHERE: обязательные программы.
SELECT id, name, description, duration_days, course_type, is_mandatory
FROM courses WHERE is_mandatory = 1 ORDER BY id;

-- name: active_trainings
-- 04. WHERE: незавершенные и неотмененные назначения.
SELECT id, employee_id, course_id, enrollment_date, is_cancelled, is_completed
FROM trainings
WHERE is_cancelled = 0 AND is_completed = 0
ORDER BY enrollment_date, id;

-- name: trainings
-- 05. JOIN: назначения со связанными сотрудниками и курсами.
SELECT t.*, e.name AS employee_name, c.name AS course_name
FROM trainings AS t
JOIN employees AS e ON e.id = t.employee_id
JOIN courses AS c ON c.id = t.course_id
ORDER BY t.enrollment_date, t.id;

-- name: results
-- 06. JOIN: итоговые оценки; отмененные/незавершенные обучения исключены.
SELECT r.*, e.name AS employee_name, c.name AS course_name
FROM results AS r
JOIN trainings AS t ON t.id = r.training_id
JOIN employees AS e ON e.id = t.employee_id
JOIN courses AS c ON c.id = t.course_id
WHERE t.is_cancelled = 0 AND t.is_completed = 1
ORDER BY r.completed_date DESC, r.id;

-- name: training_totals
-- 07. Агрегат: общее число, активные, завершенные и отмененные обучения.
SELECT COUNT(*) AS total,
       COALESCE(SUM(is_cancelled = 0 AND is_completed = 0), 0) AS active,
       COALESCE(SUM(is_cancelled = 0 AND is_completed = 1), 0) AS completed,
       COALESCE(SUM(is_cancelled = 1), 0) AS cancelled
FROM trainings;

-- name: result_summary
-- 08. Агрегат: средний, минимальный и максимальный результат.
SELECT COUNT(r.id) AS total, AVG(r.score) AS average_score,
       MIN(r.score) AS minimum_score, MAX(r.score) AS maximum_score
FROM results AS r JOIN trainings AS t ON t.id = r.training_id
WHERE t.is_cancelled = 0 AND t.is_completed = 1;

-- name: course_statistics
-- 09. GROUP BY: назначения и доля завершений по всем курсам, включая пустые.
SELECT c.id, c.name, COUNT(t.id) AS training_count,
       COALESCE(SUM(t.is_completed = 1), 0) AS completed_count,
       ROUND(100.0 * SUM(t.is_completed = 1)
             / NULLIF(COUNT(t.id), 0), 1) AS completion_rate
FROM courses AS c
LEFT JOIN trainings AS t ON t.course_id = c.id AND t.is_cancelled = 0
GROUP BY c.id, c.name ORDER BY c.id;

-- name: employee_statistics
-- 10. GROUP BY: количество оценок и средний балл каждого сотрудника.
SELECT e.id, e.name, COUNT(r.id) AS result_count,
       AVG(r.score) AS average_score
FROM employees AS e
LEFT JOIN trainings AS t ON t.employee_id = e.id
    AND t.is_cancelled = 0 AND t.is_completed = 1
LEFT JOIN results AS r ON r.training_id = t.id
GROUP BY e.id, e.name ORDER BY e.name, e.id;

-- name: popular_courses
-- 11. HAVING: курсы с минимум ? неотмененными назначениями.
SELECT c.id, c.name, COUNT(t.id) AS training_count
FROM courses AS c
JOIN trainings AS t ON t.course_id = c.id AND t.is_cancelled = 0
GROUP BY c.id, c.name HAVING COUNT(t.id) >= ?
ORDER BY training_count DESC, c.id;

-- name: available_courses
-- 12. WHERE / NOT EXISTS: курсы, доступные сотруднику ? на дату ?.
-- Завершенное назначение на ту же дату тоже блокирует повторное, как в ПР3.
SELECT c.* FROM courses AS c
WHERE NOT EXISTS (
    SELECT 1 FROM trainings AS t
    WHERE t.course_id = c.id AND t.employee_id = ?
      AND t.enrollment_date = ? AND t.is_cancelled = 0
)
ORDER BY c.id;

-- name: employee_trainings
-- 13. WHERE / JOIN: курсы и назначения конкретного сотрудника (ID = ?).
SELECT t.*, c.name AS course_name
FROM trainings AS t JOIN courses AS c ON c.id = t.course_id
WHERE t.employee_id = ? ORDER BY t.enrollment_date, t.id;

-- name: course_trainings
-- 14. WHERE / JOIN: сотрудники, которым назначен выбранный курс (ID = ?).
SELECT t.*, e.name AS employee_name
FROM trainings AS t JOIN employees AS e ON e.id = t.employee_id
WHERE t.course_id = ? ORDER BY t.enrollment_date, t.id;
