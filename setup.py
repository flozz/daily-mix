#!/usr/bin/env python

import os
from setuptools import setup, find_packages

long_description = ""

try:
    if os.path.isfile("README.rst"):
        long_description = open("README.rst", "r").read()
except Exception as error:
    print("Unable to read the README file: " + str(error))


setup(
    name="flozz-daily-mix",
    version="0.4.0",
    description="Generates thematic playlists like Spotify's Daily Mix from a Subsonic API",
    url="https://github.com/flozz/daily-mix",
    project_urls={
        "Source Code": "https://github.com/flozz/daily-mix",
        "Documentation": "https://github.com/flozz/daily-mix/blob/master/README.rst",
        "Changelog": "https://github.com/flozz/daily-mix?tab=readme-ov-file#changelog",
        "Issues": "https://github.com/flozz/daily-mix/issues",
        "Chat": "https://discord.gg/P77sWhuSs4",
        "Donate": "https://github.com/flozz/daily-mix?tab=readme-ov-file#support-this-project",
    },
    license="AGPLv3",
    long_description=long_description,
    author="Fabien LOISON",
    keywords="playlist subsonic owncloud nextcloud music",
    packages=find_packages(),
    install_requires=[],
    extras_require={
        "dev": [
            "black",
            "flake8",
            "nox",
            "pytest",
        ],
    },
    entry_points={
        "console_scripts": ["flozz-daily-mix = flozz_daily_mix.__main__:main"]
    },
)
