import re
import sys
import configparser
import logging

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
    "ignore_tracks_matching": "",
    "minimal_track_rating": 2,
    "genres": ["all"],
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
                    logging.warn("Ignored unknown setting: '[%s]%s'" % (section, key))
        elif section.startswith("playlist:"):
            playlist = dict(_DEFAULT_PLAYLIST_CONFIG)
            playlist["_id"] = section.split(":")[1].strip()
            for key in parser[section]:
                # Invaild key
                if key not in _DEFAULT_PLAYLIST_CONFIG:
                    logging.warn("Ignored unknown setting: '[%s]%s'" % (section, key))
                    continue  # TODO Write warning
                # Check regexp
                if key == "ignore_tracks_matching" and parser[section][key]:
                    try:
                        re.compile(parser[section][key])
                    except re.error as error:
                        logging.error(
                            "Invalid regexp '%s' for '[%s]%s' setting: %s"
                            % (parser[section][key], section, key, str(error))
                        )
                        sys.exit(1)
                if type(_DEFAULT_PLAYLIST_CONFIG[key]) in (list, tuple):
                    playlist[key] = [
                        item.strip() for item in parser[section][key].split(",")
                    ]
                else:
                    playlist[key] = type(_DEFAULT_PLAYLIST_CONFIG[key])(
                        parser[section][key]
                    )
            config["playlists"].append(playlist)
        elif section == "DEFAULT":
            pass  # Ignore the default section we not use...
        else:
            logging.warn("Ignored unknown configuration section: '[%s]'" % section)

    if config["subsonic/api_legacy_authentication"] is not None:
        config["subsonic/api_legacy_authentication"] = config[
            "subsonic/api_legacy_authentication"
        ].lower() in ["true", "yes", "y", "1"]

    return config
