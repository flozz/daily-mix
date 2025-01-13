#!/bin/bash

# Updates the "music.db" file used by tests (../tests/fixtures/music.db)

mkdir -p ./tests/fixtures/

python3 -m flozz_daily_mix \
    --subsonic-api-url "http://localhost:8090/apps/music/subsonic" \
    --subsonic-api-username "admin" \
    --subsonic-api-password "password" \
    --subsonic-api-legacy-authentication \
    --verbose \
    dumpdata \
    ./tests/fixtures/music.db
