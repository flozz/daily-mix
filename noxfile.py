import os
import time
import urllib.request

import nox


NEXTCLOUD_MUSIC_SUBSONIC = {
    "FZZDM_TEST_SUBSONIC_API_URL": os.environ.get(
        "FZZDM_TEST_SUBSONIC_API_URL",
        "http://localhost:8090/apps/music/subsonic",
    ),
    "FZZDM_TEST_SUBSONIC_API_USER": os.environ.get(
        "FZZDM_TEST_SUBSONIC_API_USER", "admin"
    ),
    "FZZDM_TEST_SUBSONIC_API_PASSWORD": os.environ.get(
        "FZZDM_TEST_SUBSONIC_API_PASSWORD", "password"
    ),
}

PYTHON_VERSIONS = ["3.9", "3.10", "3.11", "3.12", "3.13"]

PYTHON_FILES = [
    "flozz_daily_mix/",
    "tests/",
    "scripts/",
    "noxfile.py",
]


def _wait_for_http_backend(url, max_retry=120, verbose=True):
    """Wait for an HTTP backend getting ready.

    :param str url: The URL to test the backend readyness.
    :param int max_retry: The max retry time (in seconds).
    :param bool verbose: If True, print a message at retry (every seconds).
    """
    while max_retry:
        max_retry -= 1
        if verbose:
            print("Waiting for HTTP backend '%s' to be up..." % url)
        try:
            urllib.request.urlopen(url)
        except urllib.request.URLError as error:
            if "Connection refused" in error.reason:
                time.sleep(1)
            else:
                raise error  # Not the expected error...
        except ConnectionResetError:
            time.sleep(1)
        else:
            print("HTTP backend '%s' is up!" % url)
            break
    if not max_retry:
        raise Exception("HTTP backend '%s' never got up!" % url)


@nox.session(reuse_venv=True)
def lint(session):
    session.install("-e", ".[dev]")
    session.run("flake8", *PYTHON_FILES)
    session.run("black", "--check", "--diff", "--color", *PYTHON_FILES)
    session.run("validate-pyproject", "pyproject.toml")


@nox.session(reuse_venv=True)
def black_fix(session):
    session.install("-e", ".[dev]")
    session.run("black", *PYTHON_FILES)


@nox.session()
def start_nextcloud_docker(session):
    session.run(
        "docker",
        "build",
        "--tag",
        "fzzdm-nextcloud",
        "./tests/nextcloud/",
        external=True,
    )
    session.run(
        "docker",
        "run",
        "--rm",
        "--detach",
        "--publish",
        "8090:80",
        "--name",
        "fzzdm-test-nextcloud",
        "fzzdm-nextcloud",
        external=True,
    )
    _wait_for_http_backend("http://localhost:8090/")
    print(
        "\n→ http://localhost:8090/apps/music/#/\n  Login: admin\n  Password: password\n"
    )


@nox.session()
def stop_nextcloud_docker(session):
    session.run("docker", "stop", "fzzdm-test-nextcloud", external=True)


@nox.session(python=PYTHON_VERSIONS, reuse_venv=True)
def test(session):
    session.install("pytest")
    session.install("-e", ".")
    # fmt:off

    print("\n\n:: Run all tests excepted the Subsonic API\n\n")
    session.run(
        "pytest",
        "-m", "not subsonic",
        "--doctest-modules", "flozz_daily_mix",
        "tests/"
    )

    print("\n\n:: Run Subsonic API tests against Nextcloud Music\n\n")
    session.run(
        "pytest",
        "-m", "subsonic",
        "tests/",
        env=NEXTCLOUD_MUSIC_SUBSONIC,
    )

    # fmt:on
