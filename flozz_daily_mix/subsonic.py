import urllib.request
import urllib.parse
import json
import pathlib

from .helpers import custom_urlencode


class SubsonicClient:

    def __init__(
        self, api_base_url, username, password, client_name="FLOZz Subsonic Client/0"
    ):
        self._api_base_url = api_base_url
        self._username = username
        self._password = password
        self._client_name = client_name

    def _build_url(self, endpoint_name, **kwargs):
        parsed_base_url = urllib.parse.urlparse(self._api_base_url)

        path = pathlib.Path(parsed_base_url.path) / "rest" / endpoint_name

        query = dict(urllib.parse.parse_qsl(parsed_base_url.query))
        query["u"] = self._username
        query["p"] = self._password
        query["c"] = self._client_name
        query["v"] = "1.8.0"
        query["f"] = "json"
        query.update(kwargs)

        return urllib.parse.urlunparse(
            (
                parsed_base_url.scheme,
                parsed_base_url.netloc,
                path.as_posix(),
                parsed_base_url.params,
                custom_urlencode(query),
                parsed_base_url.fragment,
            )
        )

    def _get_json(self, url):
        http_response = urllib.request.urlopen(url)
        # TODO handle errors
        json_string = http_response.read()
        parsed_json = json.loads(json_string)
        if "subsonic-response" not in parsed_json:
            raise Exception("Invalid response from the Subsonic API")  # XXX
        if parsed_json["subsonic-response"]["status"] != "ok":
            error = ""
            if "error" in parsed_json["subsonic-response"]:
                if "message" in parsed_json["subsonic-response"]["error"]:
                    error += str(parsed_json["subsonic-response"]["error"]["message"])
                if "code" in parsed_json["subsonic-response"]["error"]:
                    error += " (code: %s)" % str(
                        parsed_json["subsonic-response"]["error"]["code"]
                    )
            raise Exception(error)  # XXX
        return parsed_json["subsonic-response"]

    def getArtists(self, **kwargs):
        query = kwargs
        url = self._build_url("getArtists", **query)
        response = self._get_json(url)
        artists = response["artists"]["index"]
        for index in artists:
            if "name" not in index:
                index["name"] = "#"
            if "artist" not in index:
                index["artist"] = []
            for i in range(len(index["artist"])):
                index["artist"][i] = {
                    "id": None,
                    "name": "Unknown artist",
                    "sortName": None,
                    "albumCount": 0,
                    "rating": None,
                    "starred": None,
                } | index["artist"][i]
        return artists

    def getAlbumList(self, type_="alphabeticalByName", offset=0, size=100, **kwargs):
        query = {"type": type_, "offset": offset, "size": size, **kwargs}
        url = self._build_url("getAlbumList", **query)
        response = self._get_json(url)
        for album in response["albumList"]["album"]:
            yield {
                "id": None,
                "parent": None,
                "artist": "Unknown artist",
                "coverArt": None,
                "title": "Unknown album",
                "sortName": None,
                "genre": "(Unknown genre)",
                "year": 0,
                "created": "1970-01-01T00:00:00.000Z",
                "rating": None,
                "starred": None,
                "isDir": True,
            } | album

    def getAlbum(self, id_=None, **kwargs):
        if not id_:
            raise ValueError()  # XXX
        query = {"id": id_, **kwargs}
        url = self._build_url("getAlbum", **query)
        response = self._get_json(url)
        album = {
            "id": None,
            "artistId": None,
            "artist": "Unknown artist",
            "coverArt": None,
            "title": "Unknown album",
            "sortName": None,
            "genre": "(Unknown genre)",
            "year": 0,
            "created": "1970-01-01T00:00:00.000Z",
            "rating": None,
            "starred": None,
            "songCount": 0,
            "duration": 0,
            "song": [],
        } | response["album"]
        for i in range(len(album["song"])):
            album["song"][i] = {
                "id": None,
                "album": "Unknown album",
                "albumId": None,
                "artist": "Unknown artist",
                "artistId": None,
                "bitRate": 0,
                "contentType": "audio/x-unknown",
                "coverArt": None,
                "created": "1970-01-01T00:00:00.000Z",
                "discNumber": 1,
                "duration": 0,
                "genre": "(Unknown genre)",
                "isVideo": False,
                "parent": None,
                "playCount": 0,
                "played": "",
                "track": 0,
                "title": "Unknown song",
                "sortName": None,
                "path": None,
                "suffix": "",
                "type": "music",
                "size": 0,
                "year": 0,
                "userRating": None,
                "starred": None,
                "isDir": False,
            } | album["song"][i]
        return album

    def getPlaylists(self, **kwargs):
        query = kwargs
        url = self._build_url("getPlaylists", **query)
        response = self._get_json(url)
        for playlist in response["playlists"]["playlist"]:
            yield {
                "id": None,
                "changed": "1970-01-01T00:00:00.000Z",
                "comment": "",
                "coverArt": None,
                "created": "1970-01-01T00:00:00.000Z",
                "duration": 0,
                "name": "Unamed Playlist",
                "owner": None,
                "public": False,
                "songCount": 0,
            } | playlist

    def createPlaylist(self, name=None, songId=[], **kwargs):
        if not name:
            raise ValueError()  # XXX
        query = {"name": name, "songId": songId, **kwargs}
        url = self._build_url("createPlaylist", **query)
        response = self._get_json(url)
        playlist = response["playlist"]
        return {
            "id": None,
            "name": "Unamed Playlist",
            "owner": None,
            "public": False,
            "changed": "1970-01-01T00:00:00.000Z",
            "comment": "",
            "coverArt": None,
            "created": "1970-01-01T00:00:00.000Z",
            "duration": 0,
            "entry": [],  # TODO enforce track fileds if we ever use them
        } | playlist

    def deletePlaylist(self, id_=None, **kwargs):
        if not id_:
            raise ValueError()  # XXX
        query = {"id": id_, **kwargs}
        url = self._build_url("deletePlaylist", **query)
        self._get_json(url)

    def updatePlaylist(
        self,
        playlistId=None,
        name=None,
        comment=None,
        public=None,
        songIdToAdd=[],
        songIndexToRemove=[],
        **kwargs
    ):
        if not playlistId:
            raise ValueError()  # XXX
        query = {
            "playlistId": playlistId,
            "songIdToAdd": songIdToAdd,
            "songIndexToRemove": songIndexToRemove,
            **kwargs,
        }
        if name is not None:
            query["name"] = name
        if comment is not None:
            query["comment"] = comment
        if public is not None:
            query["public"] = public
        url = self._build_url("updatePlaylist", **query)
        self._get_json(url)
