import re
import math
import logging
import sqlite3


_SQL_CREATE_TABLES = """

CREATE TABLE IF NOT EXISTS "artists" (
    "id"            TEXT NOT NULL UNIQUE,
    "name"          TEXT NOT NULL,
    "sortName"      TEXT,
    "starred"       INTEGER DEFAULT 0,
    "rating"        NUMERIC DEFAULT 3,
    PRIMARY KEY("id")
);

--

CREATE TABLE IF NOT EXISTS "genres" (
    "id"            INTEGER NOT NULL UNIQUE,
    "parentGenreId" INTEGER DEFAULT NULL,
    "name"          TEXT NOT NULL UNIQUE,
    PRIMARY KEY("id" AUTOINCREMENT)
);

--

CREATE TABLE IF NOT EXISTS "genre_aliases" (
    "id"            INTEGER NOT NULL UNIQUE,
    "genreId"       INTEGER DEFAULT NULL,
    "name"          TEXT NOT NULL UNIQUE,
    PRIMARY KEY("id" AUTOINCREMENT)
);

--

CREATE TABLE IF NOT EXISTS "albums" (
    "id"            TEXT NOT NULL UNIQUE,
    "artistId"      TEXT NOT NULL,
    "genreId"       TEXT,
    "coverArtId"    TEXT,
    "name"          TEXT,
    "sortName"      TEXT,
    "year"          INTEGER,
    "created"       TEXT,
    "starred"       INTEGER DEFAULT 0,
    "rating"        NUMERIC DEFAULT 3,
    PRIMARY KEY("id")
);

--

CREATE TABLE IF NOT EXISTS "tracks" (
    "id"            TEXT NOT NULL UNIQUE,
    "albumArtistId" TEXT NOT NULL,
    "artistId"      TEXT NOT NULL,
    "albumId"       TEXT NOY NULL,
    "coverArtId"    TEXT,
    "genreId"       TEXT,
    "diskNumber"    INTEGER DEFAULT 1,
    "trackNumber"   INTEGER,
    "name"          TEXT,
    "sortName"      TEXT,
    "duration"      INTERGER,
    "year"          INTEGER,
    "created"       TEXT,
    "starred"       INTEGER DEFAULT 0,
    "rating"        NUMERIC DEFAULT 3,
    "playCount"     INTERGER DEFAULT 0,
    "lastPlayed"    TEXT DEFAULT NULL,
    PRIMARY KEY("id")
);

"""


def sqlite_function_exists(cursor, name):
    """Checks if the given function is available in SQLite.

    :param cursor: SQLite cursor.
    :param str name: The function name.

    :rtype: bool

    >>> conn = sqlite3.connect(":memory:")
    >>> cur = conn.cursor()
    >>> sqlite_function_exists(cur, "foobar")
    False
    >>> sqlite_function_exists(cur, "date")
    True
    """
    response = cursor.execute(
        "SELECT 1 FROM pragma_function_list WHERE name=:name",
        {
            "name": name,
        },
    )
    return bool(response.fetchone())


class Database:

    def __init__(self, db_path=":memory:", skip_table_creation=False):
        self._db_path = db_path
        self._con = sqlite3.connect(self._db_path)
        self._cur = self._con.cursor()
        if not skip_table_creation:
            self._create_tables()
        # Add missing math functions (if SQLite was not compiled with
        # 'SQLITE_ENABLE_MATH_FUNCTIONS')
        if not sqlite_function_exists(self._cur, "log"):
            logging.debug("Adding missing math functions to SQLite...")
            self._con.create_function("log", 1, math.log10)
        # Add regexp filtering function
        self._con.create_function(
            "regexp_match", 2, lambda r, v: bool(re.match(r, v, re.I))
        )

    def _create_tables(self):
        for statement in _SQL_CREATE_TABLES.split("--"):
            self._cur.execute(statement)

    def insert_artist(
        self,
        id_=None,
        name=None,
        sortName=None,
        starred=None,
        rating=None,
    ):
        params = {k.rstrip("_"): v for k, v in locals().items()}
        query = "INSERT INTO artists VALUES(:id, :name, :sortName, :starred, :rating)"
        self._cur.execute(query, params)

    def insert_album(
        self,
        id_=None,
        artistId=None,
        genreId=None,
        coverArtId=None,
        name=None,
        sortName=None,
        year=None,
        created=None,
        starred=None,
        rating=None,
    ):
        params = {k.rstrip("_"): v for k, v in locals().items()}
        query = (
            "INSERT INTO albums VALUES(:id, :artistId, :genreId, :coverArtId, "
            ":name, :sortName, :year, :created, :starred, :rating)"
        )
        self._cur.execute(query, params)

    def insert_track(
        self,
        id_=None,
        albumArtistId=None,
        artistId=None,
        albumId=None,
        coverArtId=None,
        genreId=None,
        diskNumber=None,
        trackNumber=None,
        name=None,
        sortName=None,
        duration=None,
        year=None,
        created=None,
        starred=None,
        rating=None,
        playCount=None,
        lastPlayed=None,
    ):
        params = {k.rstrip("_"): v for k, v in locals().items()}
        query = (
            "INSERT INTO tracks VALUES(:id, :albumArtistId, :artistId, :albumId, "
            ":coverArtId, :genreId, :diskNumber, :trackNumber, :name, :sortName, "
            ":duration, :year, :created, :starred, :rating, :playCount, :lastPlayed)"
        )
        self._cur.execute(query, params)

    def execute_query(self, query, params={}):
        return self._cur.execute(query, params)

    def commit(self):
        self._con.commit()

    def __del__(self):
        self._con.close()
