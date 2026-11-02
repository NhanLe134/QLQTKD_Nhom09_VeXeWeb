import pytest
from db_utils import assert_test_database, get_test_database_url
from sqlalchemy import make_url

DEV_URL = "postgresql+asyncpg://user:pass@localhost:5432/vexe"


def test_test_url_uses_a_separate_database():
    url = get_test_database_url(DEV_URL)

    assert url.database == "vexe_test"
    assert_test_database(url, DEV_URL)


@pytest.mark.parametrize("name", ["vexe", "postgres", "vexe_test;drop", "test"])
def test_rejects_database_without_test_suffix(name):
    url = make_url(DEV_URL).set(database=name)

    with pytest.raises(RuntimeError):
        assert_test_database(url, DEV_URL)


def test_rejects_dev_database_even_if_named_like_test():
    dev_url = "postgresql+asyncpg://user:pass@localhost:5432/vexe_test"

    with pytest.raises(RuntimeError):
        assert_test_database(make_url(dev_url), dev_url)
