import pytest
from db_utils import assert_test_database, get_test_database_url
from sqlalchemy import make_url

from app.core.config import Settings

DEV_URL = "postgresql+asyncpg://user:pass@db.example.invalid:5432/postgres"
TEST_URL = "postgresql+asyncpg://user:pass@127.0.0.1:5432/vexe_test"
JWT_SECRET = "khoa-test-chi-dung-trong-pytest-du-32-ky-tu"


def settings(test_database_url: str | None, database_url: str = DEV_URL) -> Settings:
    return Settings(
        _env_file=None,
        database_url=database_url,
        test_database_url=test_database_url,
        jwt_secret=JWT_SECRET,
    )


def test_test_url_comes_from_test_database_url():
    url = get_test_database_url(settings(TEST_URL))

    assert url.database == "vexe_test"
    assert url.host == "127.0.0.1"


def test_missing_test_database_url_raises():
    with pytest.raises(RuntimeError, match="TEST_DATABASE_URL"):
        get_test_database_url(settings(None))


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1"])
def test_accepts_local_hosts(host):
    assert_test_database(make_url(TEST_URL).set(host=host), DEV_URL)


@pytest.mark.parametrize("host", ["db.example.invalid", "10.0.0.5", "postgres"])
def test_rejects_non_local_host(host):
    url = make_url(TEST_URL).set(host=host)

    with pytest.raises(RuntimeError, match="không ở máy local"):
        assert_test_database(url, DEV_URL)


@pytest.mark.parametrize("name", ["vexe", "postgres", "vexe_test;drop", "test"])
def test_rejects_database_without_test_suffix(name):
    url = make_url(TEST_URL).set(database=name)

    with pytest.raises(RuntimeError):
        assert_test_database(url, DEV_URL)


def test_rejects_test_url_equal_to_database_url():
    # Cổng mặc định 5432 vẫn bị coi là trùng
    dev_url = "postgresql+asyncpg://other:secret@127.0.0.1/vexe_test"

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        get_test_database_url(settings(TEST_URL, database_url=dev_url))
