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


class TestDBInsert:

    @pytest.fixture
    def db(self):
        db = Database(
            db_path=":memory:",
            skip_table_creation=False,
        )
        return db

    def test_insert_artist(self, db):
        default_artist = {
            "id_": "artist-1",
            "name": "Unknown artist",
            "sortName": None,
            "starred": None,
            "rating": None,
        }
        db.insert_artist(**default_artist)

    def test_insert_album(self, db):
        default_album = {
            "id_": "album-1",
            "artistId": None,
            "genreName": "(Unknown genre)",
            "coverArtId": None,
            "name": "Unknown album",
            "sortName": None,
            "year": 0,
            "created": "1970-01-01T00:00:00.000Z",
            "rating": None,
            "starred": None,
        }
        db.insert_album(**default_album)

    def test_insert_track(self, db):
        default_track = {
            "id_": "track-1",
            "albumArtistId": None,
            "artistId": None,
            "albumId": None,
            "coverArtId": None,
            "genreName": "(Unknown genre)",
            "diskNumber": 1,
            "trackNumber": 0,
            "name": "Unknown song",
            "sortName": None,
            "duration": 0,
            "year": 0,
            "created": "1970-01-01T00:00:00.000Z",
            "starred": None,
            "rating": None,
            "playCount": 0,
            "lastPlayed": "",
        }
        db.insert_track(**default_track)
