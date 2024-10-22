#!/usr/bin/env python3

"""
Updates genre from MusicBrainz DB.

USAGE:

    ./scripts/update-genres.py


WARNING:

    This script will take tens of minutes to download and extract data.
"""

import sys
import tarfile
import pathlib
import urllib.request

DB_FILES = [
    "mbdump/genre",
    "mbdump/genre_alias",
    "mbdump/l_genre_genre",
]

TMP_DIR = pathlib.Path("./build/mbdump/")
DATA_DIR = pathlib.Path("flozz_daily_mix/data/musicbrainz_db/")

MBDUMP_BASE_URL = "https://data.metabrainz.org/pub/musicbrainz/data/fullexport"
MBDUMP_LATEST_URL = "%s/LATEST" % MBDUMP_BASE_URL
MBDUMP_TARBALL_URL = "%s/%s/mbdump.tar.bz2"  # MBDUMP_BASE_URL, latest


def print_warning():
    print(
        "+----------------------------------------------------------------------+\n"
        "| WARNING                                                              |\n"
        "+----------------------------------------------------------------------+\n"
        "| This script will download the MusicBrainz database dump and extract  |\n"
        "| some useful data from it. As the archive weights more than 5 GB,     |\n"
        "| both the download and the file extraction will be very slow (several |\n"
        "| tens of minutes).                                                    |\n"
        "+----------------------------------------------------------------------+\n"
    )


def create_folders():
    print("Creating folders...")
    for folder in (TMP_DIR, DATA_DIR):
        print("  * Creating %s..." % folder.as_posix())
        folder.mkdir(parents=True, exist_ok=True)


def download_musicbrainz_db_dump():
    print("Downloading MusicBrainz DB dump files (mbdump.tar.bz2)...")

    print("  * Finding latest dump...")
    response = urllib.request.urlopen(MBDUMP_LATEST_URL)
    latest = response.read().decode("ASCII").strip()
    print("    Latest dump is: %s" % latest)

    print("  * Downloading latest dump...")
    dump_url = MBDUMP_TARBALL_URL % (MBDUMP_BASE_URL, latest)
    output_filename = TMP_DIR / "mbdump.tar.bz2"

    response = urllib.request.urlopen(dump_url)
    downloaded_length = 0
    total_length = int(response.getheader("Content-Length")) or 0

    with open(output_filename, "wb") as f:
        while chunk := response.read(1024 * 1024):
            f.write(chunk)
            downloaded_length += len(chunk)

            if total_length == 0:
                continue

            progress = downloaded_length / total_length
            sys.stdout.write(
                "\r    [%-40s] %.2f %%" % ("=" * int(progress * 40), progress * 100)
            )
            sys.stdout.flush()

    print()


def extract_musicbrainz_db_files():
    print("Extracting interesting files from MusicBrainz DB dump (mbdump.tar.bz2)...")
    with tarfile.open(TMP_DIR / "mbdump.tar.bz2", "r:bz2") as archive:
        for db_filename in DB_FILES:
            dest_filename = DATA_DIR / pathlib.Path(db_filename).name
            print("  * Extracting '%s' to '%s'..." % (db_filename, dest_filename))
            buffer = archive.extractfile(db_filename)
            with open(dest_filename, "wb") as output_file:
                output_file.write(buffer.read())


def cleanup():
    print("Removing downloaded archive...")
    archive_path = TMP_DIR / "mbdump.tar.bz2"
    archive_path.unlink()


def main():
    print_warning()
    create_folders()
    download_musicbrainz_db_dump()
    extract_musicbrainz_db_files()
    cleanup()


if __name__ == "__main__":
    main()
