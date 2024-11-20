import random
import logging
from enum import Enum


class TrackRole(Enum):
    REGULAR = "regular"
    INTEREST = "interest"
    FRESHNESS = "freshness"
    BACKCATALOG = "backcatalog"


class PlaylistGenerator:

    _SQL_SELECT_FIELDS = [
        # (Alias, Field)
        ("trackId", "tracks.id"),
        ("artistId", "tracks.artistId"),
        ("albumArtistId", "tracks.albumArtistId"),
        ("albumArtistName", "artists.name"),
        ("albumName", "albums.name"),
        ("trackName", "tracks.name"),
        ("duration", "tracks.duration"),
        ("year", "tracks.year"),
        ("rating", "tracks.rating"),
        ("starred", "tracks.starred"),
        ("playCount", "tracks.playCount"),
        ("lastPlayed", "tracks.lastPlayed"),
        ("fzzInterestScore", "%s AS fzzInterestScore"),
        ("fzzFreshnessScore", "%s AS fzzFreshnessScore"),
        ("rand", "ABS(RANDOM()) AS RAND"),
    ]

    _SQL_FROM_JOINTS = """
    FROM tracks
    LEFT JOIN artists ON artists.id = tracks.albumArtistId
    LEFT JOIN albums ON albums.id = tracks.albumId
    """

    _SQL_WHERE_CLAUSES = [
        "tracks.rating >= :min_rate",
        "tracks.duration > :min_duration",
        "tracks.duration < :max_duration",
        "NOT REGEXP_MATCH(:track_ignore_pattern, tracks.name)",
    ]

    _SQL_FRESHNESS_SCORE = """(
            (1+(LOG(366) - LOG(1+JULIANDAY('now') - MAX(JULIANDAY(tracks.created), 365))) / LOG(365))  -- recently added score
            + (1+LOG(6)-LOG(1+MIN(STRFTIME("%Y", DATE('now'))-tracks.year, 5)))  -- recently released score
            + 1+LOG(11)-LOG(1+MIN(tracks.playCount,10))  -- low play count score
           )"""

    _SQL_INTEREST_SCORE = """(
            (LOG(tracks.rating)*(1+1.2*tracks.starred))  -- rating score
            + 1+LOG(11)-LOG(1+MIN(tracks.playCount,10))  -- low play count score
           )"""

    def __init__(
        self,
        db,
        length=50,
        min_duration=60,
        max_duration=600,
        genres=["all"],
        track_ignore_pattern=None,
        min_rate=2,
    ):
        self._db = db
        self._length = length
        self._min_duration = min_duration
        self._max_duration = max_duration
        self._track_ignore_pattern = track_ignore_pattern
        self._min_rate = min_rate
        self._genres = genres
        self._genres_expanded = set()
        self._tracks_interest = {}
        self._tracks_freshness = {}
        self._tracks_backcatalog = {}
        self._tracks_regular = {}
        self._playlist = []
        self._expand_genres()

    def print(self):
        ROLES = {
            # fmt: off
            TrackRole.REGULAR:     {"symbol": "🎝", "color": "\x1B[37;44m"},
            TrackRole.INTEREST:    {"symbol": "✚", "color": "\x1B[37;43m"},
            TrackRole.FRESHNESS:   {"symbol": "❊", "color": "\x1B[37;42m"},
            TrackRole.BACKCATALOG: {"symbol": "⮜", "color": "\x1B[37;45m"},
            # fmt: on
        }
        total_duration = 0
        print(
            "%s %s %-5s %s %6s %6s %-20s %-35s \x1B[0m"
            % (
                "\x1B[1;7m",
                "R",
                "Rate",
                "S",
                "Inter.",
                "Fresh.",
                "Artist Name (Album)",
                "Track Name",
            )
        )
        for track in self._playlist:
            total_duration += track["duration"]
            print(
                "%s %s %5s %s %01.4f %01.4f %-20s %-35s \x1B[0m"
                % (
                    ROLES[track["role"]]["color"],
                    ROLES[track["role"]]["symbol"],
                    ("★" * track["rating"]) + (" " * (5 - track["rating"])),
                    "♥" if track["starred"] else "♡",
                    track["fzzInterestScore"],
                    track["fzzFreshnessScore"],
                    track["albumArtistName"][:20],
                    track["trackName"][:35],
                )
            )
        print(
            "\x1B[1;7m Total duration:\x1B[0;7m %i hr %i min %s sec \x1B[0m"
            % (
                total_duration // 3600,
                total_duration % 3600 // 60,
                total_duration % 60,
            )
        )

    def generate(self):
        self._tracks_interest = {}
        self._tracks_freshness = {}
        self._tracks_regular = {}
        self._playlist = []

        self._generate_skeleton()
        self._fetch_musics()

        prev_artist_id = None
        for i in range(self._length):
            retry_count = 3
            track = None

            # Stop if one of the music list goes empty
            if (
                not self._tracks_regular
                or not self._tracks_interest
                or not self._tracks_freshness
                or not self._tracks_backcatalog
            ):
                self._playlist = self._playlist[:i]
                break

            # Pick a track
            while retry_count:
                if self._playlist[i]["role"] == TrackRole.REGULAR:
                    track_id = random.choice(list(self._tracks_regular.keys()))
                    track = self._tracks_regular[track_id]
                elif self._playlist[i]["role"] == TrackRole.INTEREST:
                    track_id = random.choice(list(self._tracks_interest.keys()))
                    track = self._tracks_interest[track_id]
                elif self._playlist[i]["role"] == TrackRole.FRESHNESS:
                    track_id = random.choice(list(self._tracks_freshness.keys()))
                    track = self._tracks_freshness[track_id]
                elif self._playlist[i]["role"] == TrackRole.BACKCATALOG:
                    track_id = random.choice(list(self._tracks_backcatalog.keys()))
                    track = self._tracks_backcatalog[track_id]

                if track["artistId"] == prev_artist_id:
                    retry_count -= 1
                    continue
                else:
                    break

            self._playlist[i] = track
            prev_artist_id = track["artistId"]

            # Removed picked tracks from lists
            if track["trackId"] in self._tracks_regular:
                del self._tracks_regular[track["trackId"]]
            if track["trackId"] in self._tracks_interest:
                del self._tracks_interest[track["trackId"]]
            if track["trackId"] in self._tracks_freshness:
                del self._tracks_freshness[track["trackId"]]
            if track["trackId"] in self._tracks_backcatalog:
                del self._tracks_backcatalog[track["trackId"]]

    def get_playlist(self):
        return list(self._playlist)

    def get_tracks_ids(self):
        return [track["trackId"] for track in self._playlist]

    def _expand_genres(self):
        for genre in self._genres:
            if genre == "all" or not genre:
                continue
            self._genres_expanded.update(
                self._db.get_genre_subgenres(
                    genre_name=genre,
                    with_aliases=True,
                    recursive=True,
                    include_input_genre_name=True,
                )
            )

    def _generate_sql_query(
        self,
        where=[],
        order_by=[],
        limit=None,
    ):
        logging.debug("Generating SQL query...")
        sql = "    SELECT "
        sql += ",\n           ".join([f for a, f in self._SQL_SELECT_FIELDS])

        sql += "\n"
        sql += self._SQL_FROM_JOINTS.rstrip()
        sql = sql % (
            self._SQL_INTEREST_SCORE,
            self._SQL_FRESHNESS_SCORE,
        )

        if where:
            sql += "\n\n"
            sql += "    WHERE "
            sql += "\n      AND ".join(where)

        if order_by:
            sql += "\n\n"
            sql += "    ORDER BY "
            sql += ",\n             ".join(order_by)

        if limit:
            sql += "\n\n    LIMIT %i" % limit

        sql += ";"

        return sql

    def _execute_sql_query(self, query, params={}):
        logging.debug("Executing query: \n%s" % query)
        logging.debug("... with params: \n%s" % str(params))
        response = self._db.execute_query(query, params)
        for row in response.fetchall():
            yield {f[0]: v for f, v in zip(self._SQL_SELECT_FIELDS, row)}

    def _fetch_musics(self):
        params = {
            "min_rate": self._min_rate,
            "min_duration": self._min_duration,
            "max_duration": self._max_duration,
            "track_ignore_pattern": self._track_ignore_pattern,
        }

        additional_where_clauses = []

        # Handle genres
        # XXX Not very pretty to build SQL statement this way, but there is no
        # XXX good choice to parametrize a tuple/list/set...
        if len(self._genres_expanded) == 1:
            additional_where_clauses.append(
                "tracks.genreName = '%s'"
                % self._genres_expanded.copy().pop().replace("'", "''")
            )
        elif len(self._genres_expanded) > 1:
            additional_where_clauses.append(
                "tracks.genreName IN (%s)"
                % ", ".join(
                    ["'%s'" % i.replace("'", "''") for i in self._genres_expanded]
                )
            )

        # Interest
        query = self._generate_sql_query(
            where=self._SQL_WHERE_CLAUSES + additional_where_clauses,
            order_by=["fzzInterestScore DESC", "rand DESC"],
            limit=self._length // 2,
        )
        tracks = self._execute_sql_query(query, params)
        for track in tracks:
            track["role"] = TrackRole.INTEREST
            self._tracks_interest[track["trackId"]] = track

        # Freshness
        query = self._generate_sql_query(
            where=self._SQL_WHERE_CLAUSES + additional_where_clauses,
            order_by=["fzzFreshnessScore DESC", "rand DESC"],
            limit=self._length // 2,
        )
        tracks = self._execute_sql_query(query, params)
        for track in tracks:
            track["role"] = TrackRole.FRESHNESS
            self._tracks_freshness[track["trackId"]] = track

        # Back Catalog
        query = self._generate_sql_query(
            where=self._SQL_WHERE_CLAUSES
            + ["tracks.lastPlayed NOT NULL"]
            + additional_where_clauses,
            order_by=["tracks.lastPlayed", "rand DESC"],
            limit=self._length // 4,
        )
        tracks = self._execute_sql_query(query, params)
        for track in tracks:
            track["role"] = TrackRole.BACKCATALOG
            self._tracks_backcatalog[track["trackId"]] = track

        # Regular
        query = self._generate_sql_query(
            where=self._SQL_WHERE_CLAUSES + additional_where_clauses,
            order_by=["rand * tracks.rating DESC"],
            limit=self._length * 2,
        )
        tracks = self._execute_sql_query(query, params)
        for track in tracks:
            track["role"] = TrackRole.REGULAR
            self._tracks_regular[track["trackId"]] = track

    def _generate_skeleton(self):
        self._playlist = []
        next_interest = 0
        interest_spacing = 2
        max_interest_spacing = 7
        next_freshness = 1
        freshness_spacing = 2
        max_freshness_spacing = 10
        next_backcatalog = 14
        backcatalog_spacing = 14
        for i in range(self._length):
            role = TrackRole.REGULAR
            if i == next_interest:
                role = TrackRole.INTEREST
                next_interest = int(next_interest + interest_spacing)
                interest_spacing = min(interest_spacing * 1.5, max_interest_spacing)
            if i == next_freshness:
                if role == TrackRole.REGULAR:
                    role = TrackRole.FRESHNESS
                    next_freshness = int(next_freshness + freshness_spacing)
                    freshness_spacing = min(
                        freshness_spacing * 1.3, max_freshness_spacing
                    )
                else:
                    next_freshness += 1
            if i == next_backcatalog:
                if role == TrackRole.REGULAR:
                    role = TrackRole.BACKCATALOG
                    next_backcatalog += backcatalog_spacing
                else:
                    next_backcatalog += 1
            self._playlist.append(
                {
                    "role": role,
                }
            )
