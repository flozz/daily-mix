import random
from enum import Enum


class TrackRole(Enum):
    REGULAR = "regular"
    INTEREST = "interest"
    FRESHNESS = "freshness"


class PlaylistGenerator:

    def __init__(
        self,
        db,
        length=50,
        min_duration=60,
        max_duration=600,
        genres=None,
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
        self._tracks_interest = {}
        self._tracks_freshness = {}
        self._tracks_regular = {}
        self._playlist = []

    def print(self):
        ROLES = {
            # fmt: off
            TrackRole.REGULAR.value:   {"symbol": "🎝", "color": "\x1B[37;44m"},
            TrackRole.INTEREST.value:  {"symbol": "✚", "color": "\x1B[37;43m"},
            TrackRole.FRESHNESS.value: {"symbol": "❊", "color": "\x1B[37;42m"},
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
                    track["fzz_interestScore"],
                    track["fzz_freshnessScore"],
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

            # Stop if one of the music list goes empty
            if (
                not self._tracks_regular
                or not self._tracks_interest
                or not self._tracks_freshness
            ):
                self._playlist = self._playlist[: i + 1]
                break

    def get_playlist(self):
        return list(self._playlist)

    def get_tracks_ids(self):
        return [track["trackId"] for track in self._playlist]

    def _fetch_musics(self):
        # Interest
        tracks = self._db.select_random_tracks_by_interest(
            limit=self._length // 2,
            min_duration=self._min_duration,
            max_duration=self._max_duration,
            track_ignore_pattern=self._track_ignore_pattern,
            min_rate=self._min_rate,
        )
        for track in tracks:
            self._tracks_interest[track["trackId"]] = track

        # Freshness
        tracks = self._db.select_random_tracks_by_freshness(
            limit=self._length // 2,
            min_duration=self._min_duration,
            max_duration=self._max_duration,
            track_ignore_pattern=self._track_ignore_pattern,
            min_rate=self._min_rate,
        )
        for track in tracks:
            self._tracks_freshness[track["trackId"]] = track

        # Regular
        tracks = self._db.select_random_tracks(
            limit=self._length * 2,
            min_duration=self._min_duration,
            max_duration=self._max_duration,
            track_ignore_pattern=self._track_ignore_pattern,
            min_rate=self._min_rate,
        )
        for track in tracks:
            self._tracks_regular[track["trackId"]] = track

    def _generate_skeleton(self):
        self._playlist = []
        next_interest = 0
        interest_spacing = 2
        max_interest_spacing = 7
        next_freshness = 1
        freshness_spacing = 2
        max_freshness_spacing = 10
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
            self._playlist.append(
                {
                    "role": role,
                }
            )
