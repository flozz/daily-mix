import sys

from .subsonic import SubsonicClient
from .db import Database
from .playlist import PlaylistGenerator
from . import APPLICATION_NAME, VERSION


SUBSONIC_API_BASE_URL = sys.argv[1]  # FIXME debug
SUBSONIC_API_USERNAME = sys.argv[2]  # FIXME debug
SUBSONIC_API_PASSWORD = sys.argv[3]
DATABASE_FILE = "./music.db"  # FIXME debug


def get_artists(subsonic):
    for index in subsonic.getArtists():
        for artist in index["artist"]:
            yield artist


def get_albums(subsonic):
    size = 100
    offset = 0
    while albums := subsonic.getAlbumList(offset=offset, size=size):
        for album in albums:
            yield album
        offset += size


def get_tracks(subsonic):
    for album in get_albums(subsonic):
        for track in subsonic.getAlbum(album["id"])["song"]:
            track["_albumArtistId"] = album["parent"]
            track["_albumRating"] = album["rating"] if "rating" in album else 3
            yield track


def import_music_to_database(subsonic, db):
    # Get Artists
    for artist in get_artists(subsonic):
        db.insert_artist(
            id_=artist["id"],
            name=artist["name"],
            sortName=artist.get("sortName", artist["name"]),
            starred=True if "starred" in artist and artist["starred"] else False,
            rating=artist.get("rating", 3),
        )

    # Get Albums
    for album in get_albums(subsonic):
        db.insert_album(
            id_=album["id"],
            artistId=album["parent"],
            genreId=None,  # XXX
            coverArtId=album.get("coverArt", None),
            name=album["title"],
            sortName=album.get("sortName", album["title"]),
            year=album.get("year", 0),
            created=album["created"],
            starred=True if "starred" in album and album["starred"] else False,
            rating=album.get("rating", 3),  # FIXME check key name
        )

    # Get Tracks
    for track in get_tracks(subsonic):
        db.insert_track(
            id_=track["id"],
            albumArtistId=track["_albumArtistId"],
            artistId=track["artistId"],
            albumId=track["albumId"],
            coverArtId=track.get("coverArt", None),
            genreId=None,  # XXX
            diskNumber=track.get("discNumber", 1),
            trackNumber=track.get("track", 1),
            name=track["title"],
            sortName=track.get("sortName", track["title"]),
            duration=track["duration"],
            year=track.get("year", 0),
            created=track["created"],
            starred=True if "starred" in track and track["starred"] else False,
            rating=track.get("userRating", track["_albumRating"]),
            playCount=track.get("playCount", 0),
            lastPlayed=(
                track["played"] if "played" in track and track["played"] else None
            ),
        )

    db.commit()


def print_playlist(playlist):
    ROLES = {
        "regular": {"symbol": "🎝", "color": "\x1B[37;44m"},
        "interest": {"symbol": "✚", "color": "\x1B[37;43m"},
        "freshness": {"symbol": "❊", "color": "\x1B[37;42m"},
    }
    print(
        "%s %s %5s %s %6s %6s %-20s %-35s \x1B[0m"
        % (
            "\x1B[1;7m",
            "R",
            "Eval.",
            "S",
            "Inter.",
            "Fresh.",
            "Artist Name (Album)",
            "Track Name",
        )
    )
    for track in playlist:
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


def main(agrs=sys.argv[1:]):
    subsonic = SubsonicClient(
        SUBSONIC_API_BASE_URL,
        SUBSONIC_API_USERNAME,
        SUBSONIC_API_PASSWORD,
        client_name="%s/%s" % (APPLICATION_NAME, VERSION),
    )

    db = Database(DATABASE_FILE, skip_table_creation=True)  # FIXME debug
    # db = Database(DATABASE_FILE, skip_table_creation=False)  # FIXME debug
    # import_music_to_database(subsonic, db)  # FIXME debug

    generator = PlaylistGenerator(db)
    generator.generate()
    playlist = generator.get_playlist()
    print_playlist(playlist)


if __name__ == "__main__":
    main()
