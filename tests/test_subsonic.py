import os
import pytest

from flozz_daily_mix.subsonic import SubsonicClient


@pytest.mark.subsonic
@pytest.mark.skipif(
    "FZZDM_TEST_SUBSONIC_API_URL" not in os.environ,
    reason="Subsonic API params missing",
)
class TestSubsonic:

    @pytest.fixture
    def subsonic(self):
        subsonic = SubsonicClient(
            os.environ["FZZDM_TEST_SUBSONIC_API_URL"],
            os.environ["FZZDM_TEST_SUBSONIC_API_USER"],
            os.environ["FZZDM_TEST_SUBSONIC_API_PASSWORD"],
        )
        return subsonic

    def test_getArtists(self, subsonic):
        artists = subsonic.getArtists()

        # [
        #     {
        #         "name": "A"
        #         "artist": [
        #             {
        #                 "id": "artist-1",
        #                 "name": "Artist Name",
        #                 "sortName": "Name, Artist",
        #                 "albumCount": 42,
        #                 "rating": None,
        #                 "starred": None,  # "1970-01-01T00:00:00.000Z"
        #             },
        #             ...
        #         ],
        #     },
        #     ...
        # ]

        for index in artists:
            assert "name" in index
            assert "artist" in index
            assert type(index["artist"]) is list
            for artist in index["artist"]:
                assert "id" in artist
                assert "name" in artist
                assert "sortName" in artist
                assert "albumCount" in artist
                assert "rating" in artist
                assert "starred" in artist

    def test_getAlbumList(self, subsonic):
        albums = subsonic.getAlbumList()

        # [
        #     {
        #         "id": "album-1",
        #         "parent": "artist-1",  # Artist ID
        #         "artist": "Artist Name",
        #         "coverArt": "album-1",
        #         "title": "The Album Name",
        #         "sortName": "Album Name",
        #         "genre": "Genre Name",
        #         "year": 1970,
        #         "created": "1970-01-01T00:00:00.000Z",
        #         "rating": None,
        #         "starred": None,  # "1970-01-01T00:00:00.000Z"
        #         "isDir": True,
        #     },
        #     ...
        # ]

        for album in albums:
            assert "id" in album
            assert "parent" in album
            assert "artist" in album
            assert "coverArt" in album
            assert "title" in album
            assert "sortName" in album
            assert "genre" in album
            assert "year" in album
            assert "created" in album
            assert "rating" in album
            assert "starred" in album
            assert "isDir" in album and album["isDir"]

    def test_getAlbum(self, subsonic):
        for album_from_list in subsonic.getAlbumList():
            album = subsonic.getAlbum(id_=album_from_list["id"])

            # {
            #     "id": "album-1",
            #     "artistId": "artist-1",
            #     "artist": "Artist Name",
            #     "coverArt": "album-1",
            #     "name": "The Album Name",
            #     "sortName": "Album Name",
            #     "genre": "Genre Name",
            #     "year": 1970,
            #     "created": "1970-01-01T00:00:00.000Z",
            #     "rating": None,
            #     "starred": None,  # "1970-01-01T00:00:00.000Z"
            #     "songCount": 42,
            #     "duration": 3600,
            #     "song": [
            #         {
            #             "id": "track-1",
            #             "album": "The Album Name",
            #             "albumId": "album-1",
            #             "artist": "Artist Name",
            #             "artistId": "artist-1",
            #             "bitRate": 12,
            #             "contentType": "audio/ogg",
            #             "coverArt": "album-4",
            #             "created": "1970-01-01T00:00:00.000Z",
            #             "discNumber": 1,
            #             "duration": 42,
            #             "genre": "Genre Name",
            #             "isVideo": False,
            #             "parent": "album-3",
            #             "playCount": 0,
            #             "played": "",
            #             "track": 3,
            #             "title": "The Song Name",
            #             "sortName": "Song Name",
            #             "path": "/musics/album1/track1.opus",
            #             "suffix": "opus",
            #             "type": "music",
            #             "size": 47165,
            #             "year": 2011,
            #             "rating": None,
            #             "starred": None,  # "1970-01-01T00:00:00.000Z"
            #             "isDir": False,
            #         },
            #         ...
            #     ]
            # },

            assert "id" in album
            assert "artistId" in album
            assert "artist" in album
            assert "coverArt" in album
            assert "name" in album
            assert "sortName" in album
            assert "genre" in album
            assert "year" in album
            assert "created" in album
            assert "rating" in album
            assert "starred" in album
            assert "songCount" in album
            assert "duration" in album
            assert "song" in album

            for song in album["song"]:
                assert "id" in song
                assert "album" in song
                assert "albumId" in song
                assert "artist" in song
                assert "artistId" in song
                assert "bitRate" in song
                assert "contentType" in song
                assert "coverArt" in song
                assert "created" in song
                assert "discNumber" in song
                assert "duration" in song
                assert "genre" in song
                assert "isVideo" in song
                assert "parent" in song
                assert "playCount" in song
                assert "played" in song
                assert "track" in song
                assert "title" in song
                assert "sortName" in song
                assert "path" in song
                assert "suffix" in song
                assert "type" in song
                assert "size" in song
                assert "year" in song
                assert "userRating" in song
                assert "starred" in song
                assert "isDir" in song and not song["isDir"]

            assert album["songCount"] == len(album["song"])
