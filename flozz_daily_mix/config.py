import configparser

_DEFAULT_CONFIG = {
    "subsonic/api_url": None,
    "subsonic/api_username": None,
    "subsonic/api_password": None,
    "subsonic/api_legacy_authentication": None,
    "playlists": [],
}

_DEFAULT_PLAYLIST_CONFIG = {
    "_id": None,
    "name": "Unnamed Mix",
    "description": "FLOZz Daily Mix",
    "max_tracks": 60,
    "min_track_duration": 60,
    "max_track_duration": 600,
    # TODO future options to add:
    # "genres": ["all"],
    # "minimal_tracks_rating": 2,
    # "ignore_tracks_matching": "^.*(introduction|instrumental|acoustic).*$",
}


def read_config(config_files):
    config = dict(_DEFAULT_CONFIG)

    parser = configparser.ConfigParser(strict=True)
    parser.read(config_files)

    for section in parser:
        if section in ["subsonic"]:
            for key in parser[section]:
                option_name = "%s/%s" % (section, key)
                if option_name in _DEFAULT_CONFIG:
                    config[option_name] = parser[section][key]
                else:
                    pass  # TODO Write warning
        elif section.startswith("playlist:"):
            playlist = dict(_DEFAULT_PLAYLIST_CONFIG)
            playlist["_id"] = section.split(":")[1].strip()
            for key in parser[section]:
                if key not in _DEFAULT_PLAYLIST_CONFIG:
                    continue  # TODO Write warning
                playlist[key] = type(_DEFAULT_PLAYLIST_CONFIG[key])(
                    parser[section][key]
                )
            config["playlists"].append(playlist)

    if config["subsonic/api_legacy_authentication"] is not None:
        config["subsonic/api_legacy_authentication"] = config[
            "subsonic/api_legacy_authentication"
        ].lower() in ["true", "yes", "y", "1"]

    return config
