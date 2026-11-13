"""Модуль вспомогательных функций ввода и валидации.

Обеспечивает безопасный пользовательский ввод целых чисел, дат и строк.
"""

from datetime import datetime
from typing import Optional


def input_int(
    prompt: str,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
) -> int:
    """Запросить у пользователя ввод целого числа с валидацией диапазона.

    При некорректном вводе запрос повторяется.
    """
    while True:
        try:
            value = int(input(prompt).strip())
            if min_value is not None and value < min_value:
                print(f"Ошибка: число должно быть не меньше {min_value}.")
                continue
            if max_value is not None and value > max_value:
                print(f"Ошибка: число должно быть не больше {max_value}.")
                continue
            return value
        except ValueError:
            print("Ошибка: введите корректное целое число.")


def input_date(prompt: str) -> str:
    """Запросить у пользователя дату в формате ГГГГ-ММ-ДД или ДД.ММ.ГГГГ.

    Возвращает строку в каноническом формате ГГГГ-ММ-ДД.
    """
    formats = ("%Y-%m-%d", "%d.%m.%Y")
    while True:
        raw_val = input(prompt).strip()
        for fmt in formats:
            try:
                dt = datetime.strptime(raw_val, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass
        print(
            "Ошибка: неверный формат даты. "
            "Используйте ГГГГ-ММ-ДД или ДД.ММ.ГГГГ."
        )


def input_non_empty_str(prompt: str) -> str:
    """Запросить у пользователя непустую строку."""
    while True:
        val = input(prompt).strip()
        if val:
            return val
        print("Ошибка: значение не может быть пустым.")
