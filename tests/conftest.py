"""Изолированные SQLite-базы для HTTP и SQL-тестов без Django ORM."""

import os
from pathlib import Path
import shutil

import django
import pytest
from django.test import Client
from django.test import override_settings

from db.import_json import import_data

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'train_hub_dj.settings')
django.setup()


@pytest.fixture(scope='session')
def seed_database(tmp_path_factory):
    path = tmp_path_factory.mktemp('seed') / 'trainhub.sqlite'
    import_data(Path(__file__).resolve().parent.parent / 'data', path)
    return path


@pytest.fixture
def sql_database(tmp_path, seed_database):
    path = tmp_path / 'trainhub.sqlite'
    shutil.copyfile(seed_database, path)
    return path


@pytest.fixture
def client(sql_database):
    with override_settings(
        TRAINHUB_DATABASE=sql_database, TRAINHUB_DATA_BACKEND='sqlite',
    ):
        yield Client(HTTP_HOST='localhost')
