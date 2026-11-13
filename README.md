# TrainHub — система учета корпоративного обучения

Индивидуальный проект ПР1–ПР7 для HR-специалистов, руководителей и сотрудников.
Существующая консольная программа и классы предметной области сохранены.
ПР6 переводит веб-интерфейс на Django templates, ПР7 подключает SQLite через
стандартный `sqlite3`. Django ORM для предметных данных не используется.

## Установка и запуск

Используется существующее окружение Python 3.14.2, Django 6.1.2.
Зависимости перечислены в `requirements.txt`, `pyproject.toml` и `uv.lock`.
В PowerShell из корня проекта:

```powershell
.\.venv\Scripts\Activate.ps1
python -m db.import_json
python manage.py check
python manage.py runserver
```

Открыть [TrainHub](http://127.0.0.1:8000/). Предметная база уже создана:
`data/trainhub.sqlite`. Повторная команда импорта сообщает, что база заполнена,
и сохраняет данные. GET-запросы открывают SQLite только для чтения.

Если окружение еще не установлено:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m db.import_json
python manage.py runserver
```

Альтернатива с uv: `uv sync --locked`, затем `uv run python -m db.import_json`
и `uv run python manage.py runserver`.
`python manage.py migrate` относится только к уже существующим служебным
приложениям Django и базе `db.sqlite3`; схема TrainHub создается отдельно SQL.

Консоль предыдущих практических запускается командой `python main.py` и
продолжает использовать JSON. Изменения консоли автоматически в SQLite
не синхронизируются. Для демонстрации ПР6 с живыми JSON без предметной БД:

```powershell
$env:TRAINHUB_DATA_BACKEND = 'json'
python manage.py runserver
# Для следующего запуска в обычном SQL-режиме:
Remove-Item Env:TRAINHUB_DATA_BACKEND
```

Основные страницы, фильтры и проверка доступности работают в обоих режимах.
Статистика относится к ПР7: в режиме JSON ссылка скрыта, прямой адрес дает 404.

## Структура

```text
Train_hub_DJ/
├── manage.py
├── train_hub_dj/          # настройки Django, URLconf, ASGI, WSGI
├── templates/            # base.html, 404.html, includes/navigation.html
├── homepage/             # главная, статистика, загрузка связанных объектов
│   ├── templates/homepage/
│   └── static/homepage/   # css/style.css, js/main.js, img/logo.svg
├── employees/            # templates/employees/: список и карточка
├── courses/              # templates/courses/: каталог, карточка, поиск
├── trainings/            # templates/trainings/: список, карточка, includes
├── results/              # templates/results/: список и карточка
├── models/               # сохраненные User, Course, Enrollment, Result
├── storage.py            # сохраненные функции JSON
├── main.py               # сохраненная консоль
├── utils.py
├── db/
│   ├── __init__.py
│   ├── database.py        # подключения, схема, именованные SELECT
│   └── import_json.py     # атомарный импорт с executemany
├── sql/
│   ├── schema.sql
│   └── queries.sql        # 14 запросов, используемых веб-частью
├── data/                 # исходные JSON и trainhub.sqlite
├── tests/                # прежние проверки и SQL/HTTP-тесты
├── docs/                 # материалы отчетов, чек-лист, evidence/
├── requirements.txt
├── pyproject.toml
└── uv.lock
```

## Предметная область и SQLite

| Сущность | Сохраненный класс | Таблица |
| --- | --- | --- |
| Employee — сотрудник | `models.users.User` | `employees` |
| Course — курс | `models.courses.Course` | `courses` |
| Training — назначение курса | `models.enrollments.Enrollment` | `trainings` |
| Result — итоговая оценка | `models.results.Result` | `results` |

Структура таблиц определена в `sql/schema.sql`:

| Таблица | Поля и типы |
| --- | --- |
| employees | id INTEGER PK; name, email, position, role TEXT |
| courses | id INTEGER PK; name, description, course_type TEXT; duration_days, is_mandatory INTEGER |
| trainings | id INTEGER PK; employee_id, course_id INTEGER FK; enrollment_date TEXT; is_cancelled, is_completed INTEGER |
| results | id INTEGER PK; training_id INTEGER FK; score INTEGER; completed_date, comment TEXT |

Все предметные поля обязательны (`NOT NULL`), кроме объявления `INTEGER
PRIMARY KEY`, которое само задает ключ. Необязательные описание и комментарий
хранят пустую строку. Отсутствующая оценка представлена отсутствием строки
`results`, а не нулем. Агрегаты `AVG/MIN/MAX` возвращают NULL при отсутствии
оценок; шаблоны выводят «Нет оценок».

Связи: `employees 1 → N trainings`, `courses 1 → N trainings`,
`trainings 1 → N results`. Последняя связь сохраняет списки результатов ПР5;
новое ограничение «одна оценка на обучение» не вводится.
`Result.enrollment` связывает оценку с существующим объектом `Enrollment`.

Внешние ключи включаются для каждого соединения (`PRAGMA foreign_keys = ON`);
удаление используемого сотрудника, курса или обучения запрещено.
Даты хранятся как ISO `YYYY-MM-DD`. Оценка — целое 0–100, длительность — больше
нуля, логические флаги — 0 или 1. Частичный уникальный индекс запрещает два
неотмененных назначения одного курса сотруднику на одну дату, как и функция
`is_course_available()` из ПР3. Проверка на странице курса использует текущую
дату Europe/Moscow.

Триггеры проверяют при вставке/изменении результата завершенность обучения,
отсутствие отмены и дату не раньше назначения. Поздняя отмена обучения
сохраняет историю, но его результат исключается из списков и статистики,
как в JSON-реализации. Порог сдачи по оценке не выдумывается: доля завершений
считается по `is_completed` среди неотмененных назначений.

## Создание схемы и перенос JSON

```powershell
# Только создать таблицы, без заполнения:
python -c "from db.database import initialize_database; initialize_database()"
# Создать таблицы и импортировать все четыре файла:
python -m db.import_json
# Импорт в новый отдельный файл для экспериментов:
python -m db.import_json --database tmp/demo.sqlite --data-dir data
```

Пути по умолчанию абсолютные и вычисляются от каталога проекта.
`--database` указывает цель импорта; настройка веб-части задается отдельно
как `TRAINHUB_DATABASE` в `train_hub_dj/settings.py`.
Исходные `users.json`, `courses.json`, `enrollments.json`, `results.json`
не перезаписываются. Названия связей адаптируются: `user_id → employee_id`,
`enrollment_id → training_id`, идентификаторы сохраняются.

Импортер использует значения по умолчанию существующих классов и проверку
`Result`. Поврежденные JSON, отсутствующие файлы, потерянные связи и нарушения
ограничений приводят к ошибке, а не к молчаливой потере записей. Вставки через
`executemany()` выполняются в одной транзакции `BEGIN IMMEDIATE`; ошибка
откатывает все вставки. После успеха соединение фиксирует транзакцию.

Проверка заполненности и `PRAGMA user_version = 1` предотвращают повторный
импорт, включая импорт пустого набора. Автоматической очистки/перезаписи БД
нет. Для новой версии JSON можно импортировать данные в новый файл и явно
выбрать его в настройках, сохранив предыдущую базу.

Импортировано: **3 сотрудника, 3 курса, 2 обучения, 1 результат (92/100)**.
Это существующие учебные данные проекта.

## Шаблоны ПР6 и поток данных

`TEMPLATES.DIRS = [BASE_DIR / 'templates']`, `APP_DIRS = True`.
Все страницы наследуют `base.html`; `title` и `content` задаются блоками.
Общая навигация, карточка курса, таблица и статус обучения подключаются через
`include`. Использованы `for/empty`, `if/elif/else`, `length`, `default`,
`truncatechars`, `capfirst`, `yesno`, `date`, `floatformat`, `linebreaksbr`.
`app_name` и существующие имена маршрутов сохранены. Все переходы строятся
тегом `url`, файлы оформления подключены тегом `static`.
HTML автоматически экранируется Django; `safe` для пользовательских данных
не применяется. Формирование HTML через `page()` удалено из веб-представлений.

CSS и SVG находятся локально. Bootstrap 5.3.3 сохранен как дополнительный CSS
через CDN; собственный CSS обеспечивает оформление и при недоступном CDN.
Локальный JavaScript включает кнопку поиска только после выбора сотрудника и
корректной даты. Сервер также валидирует параметры, возвращая 400 при ошибке.

Поток ПР7: URL → view → `homepage/data.py` → именованный SQL из `queries.sql`
→ `sqlite3.Row` → прежние классы/контекст → `render()` → шаблон → HTML.
Статистика и поиск передают строки SQLite в контекст непосредственно.
Параметры запроса передаются через `?`, без подстановки значений в SQL-строку.

## Страницы и SQL-запросы

| URL | Назначение |
| --- | --- |
| `/` | Главная, счетчики и навигация |
| `/employees/`, `/employees/1/` | Список сотрудников, карточка и назначения |
| `/courses/`, `/courses/1/` | Каталог, карточка и доступность назначения |
| `/courses/?mandatory=1` | Только обязательные курсы |
| `/trainings/`, `/trainings/2/` | Назначения, статусы и результаты |
| `/trainings/?status=active` | Только активные обучения |
| `/results/`, `/results/1/` | Оценки и связанные объекты |
| `/courses/available/?employee=1&date=2026-10-01` | Доступные курсы для сотрудника на дату |
| `/statistics/` | Статистика по курсам и сотрудникам |

Отсутствующие ID дают оформленную 404. Для неизвестных адресов пользовательская
404 применяется при `DEBUG=False`; при `DEBUG=True` Django показывает
техническую страницу. Статика в разработке обслуживается `runserver`.

Все запросы из `sql/queries.sql` выполняются веб-слоем:

| № / имя | Тип | Задача и страница |
| --- | --- | --- |
| 01 employees | SELECT | Список сотрудников |
| 02 courses | SELECT | Каталог курсов |
| 03 mandatory_courses | WHERE | Обязательные курсы, фильтр каталога |
| 04 active_trainings | WHERE | Активные назначения, фильтр обучений |
| 05 trainings | JOIN | Связанные назначения для списков и карточек |
| 06 results | JOIN | Оценки с сотрудником и курсом |
| 07 training_totals | агрегат | Числа обучений и статусов, статистика |
| 08 result_summary | агрегат | AVG/MIN/MAX баллов, статистика |
| 09 course_statistics | GROUP BY | Назначения и доля завершений по курсам |
| 10 employee_statistics | GROUP BY | Оценки и средний балл по сотрудникам |
| 11 popular_courses | HAVING | Курсы хотя бы с одним назначением, статистика |
| 12 available_courses | WHERE/NOT EXISTS | Поиск доступных курсов по сотруднику и дате |
| 13 employee_trainings | WHERE/JOIN | Назначения выбранного сотрудника |
| 14 course_trainings | WHERE/JOIN | Сотрудники, записанные на выбранный курс |

Для количественного минимума выделены отдельные запросы 01–10: по два каждого
обязательного вида. Остальные запросы дополняют реальные сценарии.

SQLite CLI доступен без дополнительной установки через Python:

```powershell
python -m sqlite3 data/trainhub.sqlite
# В открывшемся приглашении:
# SELECT id, name FROM employees ORDER BY id;
# PRAGMA foreign_key_check;
# .quit
```

Запросы с параметрами запускать через Python:

```python
from db.database import connection, select

with connection(readonly=True) as conn:
    rows = select(conn, 'available_courses', (1, '2026-10-01'))
    print([dict(row) for row in rows])
```

## Проверки и материалы для сдачи

```powershell
python manage.py check
pytest -v
flake8 .
```

Результат проверки **02.11.2026**: системная проверка без ошибок,
**111 тестов прошли**, flake8 без замечаний. В песочнице для pytest использован
доступный временный каталог: `PYTEST_ADDOPTS=--basetemp=tmp/pytest-final`.
Тесты используют отдельные SQLite-копии, рабочую базу не изменяют.
Проверены старые классы/JSON, импорт и откат, повторный импорт, ограничения БД,
все 14 запросов, страницы/контекст/наследование, 404/400, экранирование,
статика и отсутствие записи при GET. Режим JSON проверен без SQLite-файла.
Все 14 запросов также выполнены в CLI `python -m sqlite3` с контрольными
литералами; рабочие Python-вызовы остаются параметризованными.

В браузере проверены каталог и карточка курса, поиск на 01.10.2026,
статистика и работа кнопки поиска. Сохранены реальные снимки интерфейса.
Исходные JSON, `models/`, `main.py`, `storage.py`, `utils.py` и `db.sqlite3`
сверены по SHA-256 с состоянием до работы — изменений нет.

Материалы:

- [ПР6: описание, структура и выводы](docs/PR6_report_materials.md).
- [ПР7: описание SQL-слоя и выводы](docs/PR7_report_materials.md).
- [Итоговый чек-лист по обеим методичкам](docs/PR6_PR7_checklist.md).
- [Полный вывод проверок](docs/evidence/checks.txt).
- [Результат выполнения запросов в CLI](docs/evidence/sql_cli_check.txt).
- [Каталог](docs/evidence/pr6_courses.jpg), [поиск](docs/evidence/pr7_available.jpg),
  [статистика](docs/evidence/pr7_statistics.jpg).

Упражнения Яндекс Практикума не отмечены выполненными: подтверждение в личном
кабинете отсутствует. Титульные сведения и номер варианта в материалах отчетов
нужно заполнить. Коммиты не создавались по указанию пользователя;
в текущем каталоге `.git` отсутствует. Публикация и создание репозитория
не выполнялись. Исходный проект: [TrainHub](https://github.com/Sashok999/TrainHub).
