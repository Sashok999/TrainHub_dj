"""Подключения и именованные SQL-запросы стандартного sqlite3."""

from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
import re
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'data' / 'trainhub.sqlite'
SQL_DIR = BASE_DIR / 'sql'


def get_connection(db_path=DB_PATH, *, readonly=False):
    """Открыть соединение с Row и включенными внешними ключами.

    Веб-слой использует mode=ro: GET не создает и не изменяет базу.
    """
    path = Path(db_path).resolve()
    if readonly:
        conn = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
    else:
        conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


@contextmanager
def connection(db_path=DB_PATH, *, readonly=False):
    """Зафиксировать успешную транзакцию, откатить ошибку и закрыть файл."""
    conn = get_connection(db_path, readonly=readonly)
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def initialize_database(db_path=DB_PATH):
    """Применить схему без удаления существующих таблиц или данных."""
    Path(db_path).resolve().parent.mkdir(parents=True, exist_ok=True)
    with connection(db_path) as conn:
        conn.executescript(
            'BEGIN IMMEDIATE;\n'
            + (SQL_DIR / 'schema.sql').read_text(encoding='utf-8')
            + '\nCOMMIT;'
        )


@lru_cache(maxsize=1)
def queries():
    """Загрузить SELECT из queries.sql по маркерам -- name:."""
    text = (SQL_DIR / 'queries.sql').read_text(encoding='utf-8')
    sections = re.split(r'^-- name: (\w+)\s*$', text, flags=re.MULTILINE)
    return dict(zip(sections[1::2], sections[2::2]))


def select(conn, name, parameters=()):
    """Выполнить известный запрос; значения передаются только параметрами."""
    return conn.execute(queries()[name], parameters).fetchall()
