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
