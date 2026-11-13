"""Результат завершенного обучения без использования Django ORM."""

from datetime import date


class Result:
    """Итоговая оценка, связанная с существующим назначением ПР3."""

    def __init__(
        self, result_id, enrollment, score, completed_date, comment='',
    ):
        if isinstance(score, bool) or not isinstance(score, int):
            raise ValueError('Оценка должна быть целым числом от 0 до 100.')
        if not 0 <= score <= 100:
            raise ValueError('Оценка должна быть целым числом от 0 до 100.')
        if enrollment.is_cancelled or not enrollment.is_completed:
            raise ValueError('Результат относится к завершенному обучению.')
        completion = date.fromisoformat(completed_date)
        if completion < date.fromisoformat(enrollment.enrollment_date):
            raise ValueError('Результат не может предшествовать обучению.')
        self.id = result_id
        self.enrollment = enrollment
        self.score = score
        self.completed_date = completed_date
        self.comment = comment

    def to_dict(self):
        """Сохранить связь с обучением по ID без дублирования сотрудника."""
        return {
            'id': self.id,
            'enrollment_id': self.enrollment.id,
            'score': self.score,
            'completed_date': self.completed_date,
            'comment': self.comment,
        }

    def __str__(self):
        return (
            f'Результат №{self.id}: {self.enrollment.user.name}, '
            f'{self.enrollment.course.name}, {self.score}/100'
        )


def find_result_by_id(results, result_id):
    """Найти результат по идентификатору или вернуть None."""
    return next((item for item in results if item.id == result_id), None)
