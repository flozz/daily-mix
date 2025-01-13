import os
import sys
import logging

from .subsonic import SubsonicClient
from .db import Database
from .playlist import PlaylistGenerator
from .cli import generate_cli
from .config import read_config
from .musicbrainz_db import (
    get_genres,
    get_genre_aliases,
    get_l_genre_genre,
    GENRE_LINK_TYPES,
)
from .helpers import normalize_genre_name
from . import APPLICATION_NAME, VERSION


def get_artists(subsonic):
    for index in subsonic.getArtists():
        for artist in index["artist"]:
            yield artist


def get_albums(subsonic):
    size = 100
    offset = 0
    while albums := list(subsonic.getAlbumList(offset=offset, size=size)):
        for album in albums:
            yield album
        offset += size


def get_tracks(subsonic):
    for album in get_albums(subsonic):
        for track in subsonic.getAlbum(album["id"])["song"]:
            track["_albumArtistId"] = album["parent"]
            track["_albumRating"] = album["rating"] if album["rating"] else 3
            track["_albumGenre"] = album["genre"]
            yield track


def import_music_to_database(subsonic, db):
    logging.info("Importing data from Subsonic API")
    # Get Artists
    logging.debug("  * Importing artists...")
    count = 0
    for artist in get_artists(subsonic):
        count += 1
        db.insert_artist(
            id_=artist["id"],
            name=artist["name"],
            sortName=artist["sortName"] if artist["sortName"] else artist["name"],
            starred=bool(artist["starred"]),
            rating=artist["rating"] if artist["rating"] else 3,
        )
    logging.debug("    Imported %i artist(s)." % count)

    # Get Albums
    logging.debug("  * Importing Albums...")
    count = 0
    for album in get_albums(subsonic):
        count += 1
        db.insert_album(
            id_=album["id"],
            artistId=album["parent"],
            genreName=normalize_genre_name(album["genre"]),
            coverArtId=album["coverArt"],
            name=album["title"],
            sortName=album["sortName"] if album["sortName"] else album["title"],
            year=album["year"],
            created=album["created"],
            starred=bool(album["starred"]),
            rating=album["rating"] if album["rating"] else 3,
        )
    logging.debug("    Imported %i album(s)." % count)

    # Get Tracks
    logging.debug("  * Importing Tracks...")
    count = 0
    for track in get_tracks(subsonic):
        count += 1
        db.insert_track(
            id_=track["id"],
            albumArtistId=track["_albumArtistId"],
            artistId=track["artistId"],
            albumId=track["albumId"],
            coverArtId=track["coverArt"],
            genreName=normalize_genre_name(
                track["genre"] if track["genre"] else track.get("_albumGenre", "")
            ),
            diskNumber=track["discNumber"],
            trackNumber=track["track"],
            name=track["title"],
            sortName=track["sortName"] if track["sortName"] else track["title"],
            duration=track["duration"],
            year=track["year"],
            created=track["created"],
            starred=bool(track["starred"]),
            rating=(
                track["userRating"] if track["userRating"] else track["_albumRating"]
            ),
            playCount=track["playCount"],
            lastPlayed=track["played"] if track["played"] else None,
        )
    logging.debug("    Imported %i track(s)." % count)

    db.commit()


def import_genres_to_database(db):
    logging.info("Importing genres data from Musicbrainz locale DB")

    logging.debug("  * Importing genres...")
    for genre in get_genres():
        db.insert_genre(id_=genre["id"], name=normalize_genre_name(genre["name"]))

    logging.debug("  * Importing genre aliases...")
    for alias in get_genre_aliases():
        db.insert_genre_alias(
            id_=alias["id"],
            genreId=alias["genre"],
            name=normalize_genre_name(alias["name"]),
        )

    logging.debug("  * Importing genre relations...")
    for rel in get_l_genre_genre():
        if rel["link"] == GENRE_LINK_TYPES.SUBGENRE_OF.value:
            db.insert_genre_relation(
                id_=rel["id"], parentGenreId=rel["entity0"], childGenreId=rel["entity1"]
            )
        if rel["link"] == GENRE_LINK_TYPES.FUSION_OF.value:
            db.insert_genre_relation(
                id_=rel["id"], parentGenreId=rel["entity1"], childGenreId=rel["entity0"]
            )

    db.commit()


def create_or_update_playlsit(
    subsonic,
    fzz_id,
    name="Unnamed Mix",
    comment="",
    tracks_ids=[],
):
    fzz_id_tag = "{FZz:%s}" % str(fzz_id)
    playlist_id = None
    playlist_track_count = 0

    # Search if the playlist already exists
    for playlist in subsonic.getPlaylists():
        if fzz_id_tag in playlist["comment"]:
            playlist_id = playlist["id"]
            playlist_track_count = playlist["songCount"]

    # Create the playlist if does not exists
    if playlist_id is None:
        logging.debug("Creating the '%s' playlist via Subsonic API..." % name)
        playlist = subsonic.createPlaylist(name=name)
        playlist_id = playlist["id"]

    # Empty the playlist if required
    if playlist_track_count > 0:
        logging.debug("Updating the '%s' playlist via Subsonic API..." % name)
        subsonic.updatePlaylist(
            playlistId=playlist_id,
            songIndexToRemove=list(range(playlist_track_count)),
        )

    # Update the playlist with the new tracks
    subsonic.updatePlaylist(
        playlistId=playlist_id,
        name=name,
        comment="\n\n".join([comment, fzz_id_tag]),
        songIdToAdd=tracks_ids,
    )


def dumpdata(subsonic, db_file):
    logging.info("Dumping data from Subsonic API to '%s'..." % db_file)
    # Remove the database file if it already exists. We cannot update it, we
    # can only dump all data again.
    if os.path.isfile(db_file):
        logging.debug("Removing existing database...")
        os.unlink(db_file)

    # Create the database
    logging.debug("Creating new database...")
    db = Database(db_file)

    # Fetch data from the music cloud
    import_music_to_database(subsonic, db)

    # Import genres from Musicbrainz locale db
    import_genres_to_database(db)


def generate(subsonic, playlists_configs, db_file=None, dry_run=False, print_pl=False):
    if db_file:
        db = Database(db_file, skip_table_creation=True)
    else:
        db = Database(":memory:")

    # Fetch data from the music cloud and import genres if no input database provided
    if not db_file:
        import_music_to_database(subsonic, db)
        import_genres_to_database(db)

    # Generate playlists from configs
    for playlist_config in playlists_configs:
        logging.info("Generating '%s' playlist..." % playlist_config["name"])

        logging.debug("Playlist config:")
        for k, v in playlist_config.items():
            logging.debug("  * %s: %s" % (k, str(playlist_config[k])))

        # Check genres exists and warn the user if they don't
        for genre in playlist_config["genres"]:
            if not db.is_genre(genre) and not db.is_genre_alias(genre):
                logging.warning("The genre '%s' is unknown" % genre)

        generator = PlaylistGenerator(
            db,
            length=playlist_config["max_tracks"],
            min_duration=playlist_config["min_track_duration"],
            max_duration=playlist_config["max_track_duration"],
            track_ignore_pattern=playlist_config["ignore_tracks_matching"],
            min_rate=playlist_config["minimal_track_rating"],
            genres=[normalize_genre_name(genre) for genre in playlist_config["genres"]],
        )
        generator.generate()

        if print_pl:
            generator.print()

        if not dry_run:
            create_or_update_playlsit(
                subsonic,
                playlist_config["_id"],
                name=playlist_config["name"],
                comment=playlist_config["description"],
                tracks_ids=generator.get_tracks_ids(),
            )
        else:
            logging.debug(
                "Playlist '%s' not saved to the Subsonic API (dry-run)"
                % playlist_config["name"]
            )


def list_genres(db_file=None):
    if db_file:
        db = Database(db_file, skip_table_creation=True)
    else:
        db = Database(":memory:")

    # Import genres if no input database provided
    if not db_file:
        import_genres_to_database(db)

    def _print_genre_tree(genres, level=0, prefix=""):
        for genre in genres:
            bullet = "├"
            next_prefix = "│ "
            if genres.index(genre) == len(genres) - 1:
                bullet = "└"
                next_prefix = "  "
            elif level == 0 and genres.index(genre) == 0:
                bullet = "┌"
            print(
                "\x1B[2;90m%s%s╴\x1B[0m%s \x1B[2m%s\x1B[0m"
                % (
                    prefix,
                    bullet,
                    genre["name"].title(),
                    (
                        "(%s)"
                        % ", ".join(
                            genre["aliases"],
                        )
                        if genre["aliases"]
                        else ""
                    ),
                )
            )
            _print_genre_tree(genre["children"], level + 1, prefix=prefix + next_prefix)

    _print_genre_tree(db.get_genre_tree())


def setup_logging(level):
    if level <= logging.DEBUG:
        logging.basicConfig(
            format="[%(asctime)s] %(levelname)7s: %(message)s",
            level=level,
        )
    else:
        logging.basicConfig(
            format="%(levelname)s: %(message)s",
            level=level,
        )


def main(args=sys.argv[1:]):
    parser = generate_cli()
    parsed_args = parser.parse_args(args if args else ["--help"])

    # Setup logging
    log_level = logging.INFO
    if parsed_args.quiet:
        log_level = logging.ERROR
    elif parsed_args.verbose:
        log_level = logging.DEBUG
    setup_logging(log_level)
    logging.debug("Log level is set to %s" % logging.getLevelName(log_level))

    # Check we have a subcomand
    if not parsed_args.subcommand:
        logging.error("No subcomand provided. Use the --help option to get help.")
        sys.exit(1)

    # Subsonic API configuration and credentials
    subsonic_api_url = parsed_args.subsonic_api_url
    subsonic_api_username = parsed_args.subsonic_api_username
    subsonic_api_password = parsed_args.subsonic_api_password
    subsonic_api_legacy_authentication = parsed_args.subsonic_api_legacy_authentication

    # In some cases there will be no access to the Subsonic API, so there will
    # be no need for a Subsonic instance nor to check if we have credentials set
    skip_subsonic = False
    if (
        parsed_args.subcommand == "generate"
        and parsed_args.source_db
        and parsed_args.dry_run
    ):
        skip_subsonic = True
    elif parsed_args.subcommand == "genres":
        skip_subsonic = True

    # Parse config
    config_files = []
    if hasattr(parsed_args, "config_file") and parsed_args.config_file:
        config_files = parsed_args.config_file
        if type(config_files) is str:
            config_files = [config_files]
    config = read_config(config_files)

    # Update credentials from config
    if subsonic_api_url is None and config["subsonic/api_url"] is not None:
        subsonic_api_url = config["subsonic/api_url"]

    if subsonic_api_username is None and config["subsonic/api_username"] is not None:
        subsonic_api_username = config["subsonic/api_username"]

    if subsonic_api_password is None and config["subsonic/api_password"] is not None:
        subsonic_api_password = config["subsonic/api_password"]

    if (
        subsonic_api_legacy_authentication is False
        and config["subsonic/api_legacy_authentication"] is not None
    ):
        subsonic_api_legacy_authentication = config[
            "subsonic/api_legacy_authentication"
        ]

    # Print configs
    logging.debug("Subcommand: %s" % parsed_args.subcommand)
    logging.debug("Subsonic API:")
    logging.debug("  * URL: %s" % subsonic_api_url)
    logging.debug("  * Username: %s" % subsonic_api_username)
    logging.debug(
        "  * Password: %s"
        % ("*" * len(subsonic_api_password) if subsonic_api_password else "-none-")
    )
    logging.debug(
        "  * Use legacy authentication: %s"
        % ("True" if subsonic_api_legacy_authentication else "False")
    )
    logging.debug("General Options:")
    logging.debug("  * quiet: %s" % ("True" if parsed_args.quiet else "False"))
    logging.debug("  * verbose: %s" % ("True" if parsed_args.verbose else "False"))
    if parsed_args.subcommand == "generate":
        logging.debug("Generate Options:")
        logging.debug("  * dry_run: %s" % ("True" if parsed_args.dry_run else "False"))
        logging.debug(
            "  * print_playlist: %s"
            % ("True" if parsed_args.print_playlist else "False")
        )
        logging.debug("  * source_db: %s" % str(parsed_args.source_db))
        logging.debug("  * skip_subsonic: %s" % ("True" if skip_subsonic else "False"))
        logging.debug("  * config_files: %s" % ", ".join(parsed_args.config_file))
    if parsed_args.subcommand == "dumpdata":
        logging.debug("Dumpdata Options:")
        logging.debug("  * config_files: %s" % str(parsed_args.config_file))
        logging.debug("  * db_file: %s" % str(parsed_args.db_file))

    # Check we have the config and the credentials for the Subsonic API
    if not skip_subsonic:
        if not subsonic_api_url:
            logging.error("No Subsonic API URL configured.")
            sys.exit(1)

        if not subsonic_api_username:
            logging.error("No username provided for the Subsonic API authentication.")
            sys.exit(1)

        if not subsonic_api_password:
            logging.error("No password provided for the Subsonic API authentication.")
            sys.exit(1)

        # FIXME
        # The '--subsonic-api-legacy-authentication' option is mandatory to be
        # futur-proof (no API change when the newer method will be implemented).
        # Curently we only support Nextcloud Music and its legacy plain-text
        # password auth.
        if not subsonic_api_legacy_authentication:
            logging.error(
                "New Subsonic API authentication method is not supported yet. "
                "Please use the '--subsonic-api-legacy-authentication' option."
            )
            sys.exit(1)

    # Initialize Subsonic client
    subsonic = None
    if not skip_subsonic:
        subsonic = SubsonicClient(
            subsonic_api_url,
            subsonic_api_username,
            subsonic_api_password,
            client_name="%s/%s" % (APPLICATION_NAME, VERSION),
        )

    # Run the requested task
    if parsed_args.subcommand == "generate":
        generate(
            subsonic,
            config["playlists"],
            db_file=parsed_args.source_db,
            dry_run=parsed_args.dry_run,
            print_pl=parsed_args.print_playlist,
        )
    elif parsed_args.subcommand == "dumpdata":
        dumpdata(subsonic, parsed_args.db_file)
    elif parsed_args.subcommand == "genres":
        list_genres(db_file=parsed_args.source_db)


if __name__ == "__main__":
    main()
