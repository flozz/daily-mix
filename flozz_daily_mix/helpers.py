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
