import re
import math
import logging
import sqlite3

from .helpers import normalize_genre_name


# SQL Queries to create the tables. Each creation statement should be separated
# by a line containing only two dash and a line feed char ("--\n").
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

CREATE TABLE IF NOT EXISTS "genre_relations" (
    "id"            INTEGER NOT NULL UNIQUE,
    "parentGenreId" INTEGER DEFAULT NULL,
    "childGenreId"  INTEGER DEFAULT NULL,
    PRIMARY KEY("id" AUTOINCREMENT)
);

--

CREATE TABLE IF NOT EXISTS "albums" (
    "id"            TEXT NOT NULL UNIQUE,
    "artistId"      TEXT NOT NULL,
    "genreName"     TEXT,
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
    "genreName"     TEXT,
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
        genreName=None,
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
            "INSERT INTO albums VALUES(:id, :artistId, :genreName, :coverArtId, "
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
        genreName=None,
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
            ":coverArtId, :genreName, :diskNumber, :trackNumber, :name, :sortName, "
            ":duration, :year, :created, :starred, :rating, :playCount, :lastPlayed)"
        )
        self._cur.execute(query, params)

    def insert_genre(self, id_=None, name=None):
        params = {k.rstrip("_"): v for k, v in locals().items()}
        query = "INSERT INTO genres VALUES(:id, :name)"
        self._cur.execute(query, params)

    def insert_genre_alias(self, id_=None, genreId=None, name=None):
        params = {k.rstrip("_"): v for k, v in locals().items()}
        query = "INSERT INTO genre_aliases VALUES(:id, :genreId, :name)"
        self._cur.execute(query, params)

    def insert_genre_relation(self, id_=None, parentGenreId=None, childGenreId=None):
        params = {k.rstrip("_"): v for k, v in locals().items()}
        query = "INSERT INTO genre_relations VALUES(:id, :parentGenreId, :childGenreId)"
        self._cur.execute(query, params)

    def is_genre(self, genre_name):
        """Check if the given genre name is an existing genre.

        .. NOTE::

           The given genre name will be normalized.

        :param str genre_name: The genre name.

        rtype: bool
        """
        params = {"genre_name": normalize_genre_name(genre_name)}
        query = "SELECT COUNT() AS count FROM genres WHERE genres.name = :genre_name;"
        self._cur.execute(query, params)
        return bool(self._cur.fetchone()[0])

    def is_genre_alias(self, genre_name):
        """Check if the given genre name is an existing genre alias.

        .. NOTE::

           The given genre name will be normalized.

        :param str genre_name: The genre name.

        rtype: bool
        """
        params = {"genre_name": normalize_genre_name(genre_name)}
        query = "SELECT COUNT() AS count FROM genre_aliases WHERE genre_aliases.name = :genre_name;"
        self._cur.execute(query, params)
        return bool(self._cur.fetchone()[0])

    def get_genre_aliases(self, *, genre_name=None, genre_id=None):
        """Returns name aliases of the given genre.

        :param str genre_name: The name of the parent genre we are searching
            the subgenre for (optional BUT one of 'genre_name' or 'genre_id'
            param must be defined).
        :param str genre_name: The id of the parent genre we are searching the
            subgenre for (optional BUT one of 'genre_name' or 'genre_id' param
            must be defined).

        .. IMPORTANT::

            Either ``genre_name`` or ``genre_id`` must be defined but not both!

        :rtype: generator<str>
        """
        if (
            genre_name is None
            and genre_id is None
            or genre_name is not None
            and genre_id is not None
        ):
            raise ValueError("Either 'genre_name' or 'genre_id' must be defined")

        if not genre_id:
            params = {"genreName": genre_name}
            query = "SELECT id FROM genres WHERE name = :genreName"
            self._cur.execute(query, params)
            response = self._cur.fetchone()
            if response:
                (genre_id,) = response

        params = {"genreId": genre_id}
        query = "SELECT genre_aliases.name FROM genre_aliases WHERE genre_aliases.genreId = :genreId"
        self._cur.execute(query, params)

        for (alias,) in self._cur.fetchall():
            yield alias

    def get_genre_subgenres(
        self,
        *,
        genre_name=None,
        genre_id=None,
        with_aliases=False,
        recursive=False,
        include_input_genre_name=True,
    ):
        """Returns subgenre of the given genre.

        :param str genre_name: The name of the parent genre we are searching
            the subgenre for (optional BUT one of 'genre_name' or 'genre_id'
            param must be defined).
        :param str genre_name: The id of the parent genre we are searching the
            subgenre for (optional BUT one of 'genre_name' or 'genre_id' param
            must be defined).
        :param bool with_aliases: Whether to includes name aliases of the given
            genre and found subgenres or not (default: ``False``).
        :param bool recursive: Include recursively names (and aliases if
            ``with_aliases`` is ``True``) of subgenres (default: ``False``).
        :param bool include_input_genre_name: Whether to include the input
            genre name (when ``genre_name`` provided) or not (default:
            ``True``).

        .. IMPORTANT::

            Either ``genre_name`` or ``genre_id`` must be defined but not both!

        :rtype: generator<str>
        """
        if (
            genre_name is None
            and genre_id is None
            or genre_name is not None
            and genre_id is not None
        ):
            raise ValueError("Either 'genre_name' or 'genre_id' must be defined")

        genre_alias = None

        # Find genre id
        if not genre_id:
            params = {"genreName": genre_name}
            query = "SELECT id FROM genres WHERE name = :genreName"
            self._cur.execute(query, params)
            response = self._cur.fetchone()
            if response:
                (genre_id,) = response
            else:
                # Handle the genre name as an alias
                genre_alias = genre_name
                genre_name = None

        # Handle aliases as input
        if genre_alias:
            params = {"aliasName": genre_alias}
            query = "SELECT genreId FROM genre_aliases WHERE name = :aliasName"
            self._cur.execute(query, params)
            response = self._cur.fetchone()
            if response:
                (genre_id,) = response
                # Get real genre name
                params = {"genreId": genre_id}
                query = "SELECT name FROM genres WHERE id = :genreId"
                self._cur.execute(query, params)
                response = self._cur.fetchone()
                if response:
                    (genre_name,) = response

        if include_input_genre_name and genre_name:
            yield genre_name
            if not genre_id:
                return
        elif include_input_genre_name and genre_alias:
            yield genre_alias
            if not genre_id:
                return
        elif not genre_id:
            return []

        if with_aliases:
            for alias in self.get_genre_aliases(genre_id=genre_id):
                yield alias

        params = {"parentGenreId": genre_id}
        query = """
        SELECT genres.id, genres.name
        FROM genre_relations
        LEFT JOIN genres ON genres.id = genre_relations.childGenreId
        WHERE genre_relations.parentGenreId = :parentGenreId
        """
        self._cur.execute(query, params)

        for subgenre_id, subgenre_name in self._cur.fetchall():
            yield subgenre_name
            if with_aliases:
                for alias in self.get_genre_aliases(genre_id=subgenre_id):
                    yield alias
            if recursive:
                for subsubgenre_name in self.get_genre_subgenres(
                    genre_id=subgenre_id, recursive=True
                ):
                    yield subsubgenre_name

    def get_genre_tree(self):
        genre_tree = []

        # Find root genres
        params = {}
        query = """
        SELECT genres.id AS genreId,
               genres.name as genreName,
               genre_relations.parentGenreId as parentGenreId
        FROM genres
        LEFT JOIN genre_relations ON genres.id = genre_relations.childGenreId
        WHERE parentGenreId IS NULL
        ORDER BY genreName ASC
        """
        self._cur.execute(query, params)

        for genreId, genreName, parentGenreId in self._cur.fetchall():
            genre_tree.append(
                {
                    "name": genreName,
                    "children": [],
                    "aliases": list(self.get_genre_aliases(genre_name=genreName)),
                }
            )

        def _recursive_subgenre_list(root_genres):
            for genre in root_genres:
                genre["children"] = [
                    {
                        "name": sg,
                        "children": [],
                        "aliases": list(self.get_genre_aliases(genre_name=sg)),
                    }
                    for sg in self.get_genre_subgenres(
                        genre_name=genre["name"],
                        with_aliases=False,
                        recursive=False,
                        include_input_genre_name=False,
                    )
                ]
                _recursive_subgenre_list(genre["children"])

        _recursive_subgenre_list(genre_tree)

        return genre_tree

    def execute_query(self, query, params={}):
        return self._cur.execute(query, params)

    def commit(self):
        self._con.commit()

    def __del__(self):
        self._con.close()
