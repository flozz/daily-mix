import re
import pathlib
import urllib.parse


def custom_urlencode(params):
    """A custom version of urllib.parse.urlencode that encodes lists and tuple
    by repeating the key for each item.

    >>> custom_urlencode({"foo": ["bar", "baz", "pwet"]})
    'foo=bar&foo=baz&foo=pwet'
    >>> custom_urlencode({"foo": ("bar", "baz", "pwet")})
    'foo=bar&foo=baz&foo=pwet'
    >>> custom_urlencode({"foo": "bar", "fizz": "buzz"})
    'foo=bar&fizz=buzz'
    >>> custom_urlencode({"foo": []})
    ''
    """
    components = []

    for key, value in params.items():
        if type(value) in [list, tuple]:
            for item in value:
                components.append(urllib.parse.urlencode({key: item}))
        else:
            components.append(urllib.parse.urlencode({key: value}))

    return "&".join(components)


def get_data_file_path(filename):
    """Get the path of a data file.

    :param str filename: The name of the data file.

    :rtype: pathlib.Path

    >>> get_data_file_path("musicbrainz_db/genre")
    PosixPath('.../flozz_daily_mix/data/musicbrainz_db/genre')
    """
    root = pathlib.Path(__file__).parent
    return root / "data" / filename


def normalize_genre_name(genre):
    """Try to normalize the given gnre by removing extra-spaces, converting it
    to lower case,...

    :param str genre: The genre name.

    :rtype: str

    >>> normalize_genre_name(" Rock ")
    'rock'
    >>> normalize_genre_name(" Celtic  Rock; Folk Rock ")
    'celtic rock'
    >>> normalize_genre_name("post_punk")
    'post punk'
    """
    for separator in (";", ",", "|"):
        if separator in genre:
            genre = genre.split(separator)[0]
    genre = genre.strip()
    genre = genre.lower()
    genre = re.sub(r"[\s _]+", " ", genre)
    genre = re.sub(r"[-–—]+", "-", genre)
    return genre
