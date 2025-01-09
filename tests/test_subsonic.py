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
