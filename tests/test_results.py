"""Проверки новой сущности и сохранения связи с объектами ПР3."""

import json

import pytest

from models import Course, Enrollment, Result, User
from models.results import find_result_by_id
from storage import load_results, save_results


@pytest.fixture
def completed_training():
    return Enrollment(
        1, Course(1, 'Охрана труда', '', 3), '2026-10-01',
        User(1, 'Иван Иванов', 'ivanov@example.com'), is_completed=True,
    )


def test_result_roundtrip_preserves_links(tmp_path, completed_training):
    result = Result(1, completed_training, 92, '2026-10-04', 'Тестирование')
    filename = tmp_path / 'results.json'
    save_results(filename, [result])
    loaded = load_results(filename, [completed_training])
    assert len(loaded) == 1
    assert loaded[0].enrollment is completed_training
    assert loaded[0].enrollment.user.name == 'Иван Иванов'
    assert loaded[0].to_dict() == result.to_dict()
    assert find_result_by_id(loaded, 1) is loaded[0]
    assert find_result_by_id(loaded, 999) is None


@pytest.mark.parametrize('score', [-1, 101, True, 3.5, '92'])
def test_invalid_score_is_rejected(completed_training, score):
    with pytest.raises(ValueError):
        Result(1, completed_training, score, '2026-10-04')


@pytest.mark.parametrize('score', [0, 100])
def test_score_boundaries(completed_training, score):
    assert Result(1, completed_training, score, '2026-10-04').score == score


@pytest.mark.parametrize('value', ['2026-09-30', '2026-02-30', 'не дата'])
def test_invalid_completion_date_is_rejected(completed_training, value):
    with pytest.raises(ValueError):
        Result(1, completed_training, 92, value)


def test_only_completed_training_can_have_result(completed_training):
    completed_training.is_completed = False
    with pytest.raises(ValueError):
        Result(1, completed_training, 92, '2026-10-04')
    completed_training.is_completed = True
    completed_training.cancel()
    with pytest.raises(ValueError):
        Result(1, completed_training, 92, '2026-10-04')


def test_invalid_results_are_skipped(tmp_path, completed_training):
    valid = Result(1, completed_training, 92, '2026-10-04').to_dict()
    records = [dict(valid, enrollment_id=999), {}, None, valid]
    filename = tmp_path / 'results.json'
    filename.write_text(json.dumps(records), encoding='utf-8')
    loaded = load_results(filename, [completed_training])
    assert [item.id for item in loaded] == [1]
    assert load_results(tmp_path / 'missing.json', [completed_training]) == []
    filename.write_text('{broken', encoding='utf-8')
    assert load_results(filename, [completed_training]) == []
