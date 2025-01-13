import pytest

from flozz_daily_mix.db import Database


class TestDB:

    @pytest.fixture
    def db(self):
        db = Database(
            db_path="./tests/fixtures/music.db",
            skip_table_creation=True,
        )
        return db

    def test_is_genre(self, db):
        assert db.is_genre("rock")
        assert db.is_genre("Rock")
        assert db.is_genre(" Rock ")
        assert not db.is_genre("XXX NOT A GENRE")

    def test_is_genre_alias(self, db):
        assert db.is_genre_alias("rock music")
        assert db.is_genre_alias("Rock Music")
        assert db.is_genre_alias(" Rock music ")
        assert not db.is_genre_alias("XXX NOT A GENRE ALIAS")
