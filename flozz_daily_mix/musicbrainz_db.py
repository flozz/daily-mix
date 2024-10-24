import csv
from enum import IntEnum

from .helpers import get_data_file_path


# Original table name: genre
# Schema: https://wiki.musicbrainz.org/images/a/ac/genre_entity_details.svg
COLUMNS_GENRE = {
    "id": int,
    "gid": str,  # UUIDv4
    "name": str,
    "comment": str,
    "edits_pending": int,
    "last_updated": str,  # date
}

# Original table name: genre_alias
# Schema: https://wiki.musicbrainz.org/images/a/ac/genre_entity_details.svg
COLUMNS_GENRE_ALIAS = {
    "id": int,
    "genre": int,  # genre id
    "name": str,
    "locale": str,  # e.g. "en"
    "edits_pending": int,
    "last_updated": str,  # date
    "type": int,  # genre alias type id
    "sort_name": str,
    "begin_date_year": None,  # None (\N)
    "begin_date_month": None,  # None (\N)
    "begin_date_day": None,  # None (\N)
    "end_date_year": None,  # None (\N)
    "end_date_month": None,  # None (\N)
    "end_date_day": None,  # None (\N)
    "primary_for_locale": None,  # bool: False (f)
    "ended": None,  # bool: False (f)
}


# Original table name: l_genre_genre
# Schema: https://wiki.musicbrainz.org/images/2/2c/relationship_overview.svg
COLUMNS_L_GENRE_GENRE = {
    "id": int,
    "link": int,  # link id, a.k.a link types, see 'GENRE_LINK_TYPES' bellow
    "entity0": int,  # genre id
    "entity1": int,  # genre id
    "edits_pending": int,
    "last_updated": str,  # date
    "link_order": int,
    "entity0_credit": str,
    "entity1_credit": str,
}


# There is only 3 relevent link types for genres so here there are (no need to
# include the whole link database for that)
class GENRE_LINK_TYPES(IntEnum):
    """Link types between genres in MusicBrainz DB."""

    SUBGENRE_OF = 944810
    FUSION_OF = 944812
    INFLUENCED_BY = 944813


class PgDumpDialect(csv.Dialect):
    """CSV dialect to parse dumps of PostgreSQL databases."""

    delimiter = "\t"
    lineterminator = "\n"
    quoting = csv.QUOTE_NONE
    strict = True


csv.register_dialect("pgdump", PgDumpDialect)


def _cast_row(row, fields):
    """Casts data of the row.

    :param dict row: The row to cast (``{"key": "value"}``)
    :param dict fields: The descriptions of the fields (``{"field_name": type}``)

    :rtype: dict
    """
    return {
        k: fields[k](v) if fields[k] is not None and v != "\\N" else None
        for (k, v) in row.items()
    }


def get_genres():
    """Returns genres from MusicBrainz DB.

    :rtype: list<dict>

    Example data::

        [
            {
                "id": 14,
                "gid": "ceeaa283-5d7b-4202-8d1d-e25d116b2a18",
                "name": "alternative rock",
                "comment": "",
                "edits_pending": 0,
                "last_updated": "2019-05-13 17:46:28.122726+00",
            },
        ]
    """
    db_path = get_data_file_path("musicbrainz_db/genre")
    with open(db_path, "r") as f:
        reader = csv.DictReader(f, fieldnames=COLUMNS_GENRE, dialect="pgdump")
        return [_cast_row(r, COLUMNS_GENRE) for r in reader]


def get_genre_aliases():
    """Returns genres aliases from MusicBrainz DB.

    :rtype: list<dict>

    Example data::

        [
            {
                "id": 227,
                "genre": 124,
                "name": "electronic body music",
                "locale": "en",
                "edits_pending": 0,
                "last_updated": "2022-07-01 10:32:15.084882+00",
                "type": 1,
                "sort_name": "electronic body music",
                "begin_date_year": None,
                "begin_date_month": None,
                "begin_date_day": None,
                "end_date_year": None,
                "end_date_month": None,
                "end_date_day": None,
                "primary_for_locale": None,
                "ended": None,
            },
        ]
    """
    db_path = get_data_file_path("musicbrainz_db/genre_alias")
    with open(db_path, "r") as f:
        reader = csv.DictReader(f, fieldnames=COLUMNS_GENRE_ALIAS, dialect="pgdump")
        return [_cast_row(r, COLUMNS_GENRE_ALIAS) for r in reader]


def get_l_genre_genre():
    """Returns links between genres from MusicBrainz DB.

    :rtype: list<dict>

    Example data::

        [
            {
                "id": 3206,
                "link": 944810,
                "entity0": 1560,
                "entity1": 2132,
                "edits_pending": 0,
                "last_updated": "2024-08-10 05:57:55.491593+00",
                "link_order": 0,
                "entity0_credit": "",
                "entity1_credit": "",
            },
        ]
    """
    db_path = get_data_file_path("musicbrainz_db/l_genre_genre")
    with open(db_path, "r") as f:
        reader = csv.DictReader(f, fieldnames=COLUMNS_L_GENRE_GENRE, dialect="pgdump")
        return [_cast_row(r, COLUMNS_L_GENRE_GENRE) for r in reader]
