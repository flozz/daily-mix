import time
import urllib.request

import nox

PYTHON_FILES = [
    "flozz_daily_mix",
    "scripts",
    "noxfile.py",
    "setup.py",
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
    session.install("flake8", "black")
    session.run("black", "--check", "--diff", "--color", *PYTHON_FILES)
    session.run("flake8", *PYTHON_FILES)


@nox.session(reuse_venv=True)
def black_fix(session):
    session.install("black")
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
        "fzzdm-test-nexcloud",
        "fzzdm-nextcloud",
        external=True,
    )
    _wait_for_http_backend("http://localhost:8090/")
    print(
        "\n→ http://localhost:8090/apps/music/#/\n  Login: admin\n  Password: password\n"
    )


@nox.session()
def stop_nextcloud_docker(session):
    session.run("docker", "stop", "fzzdm-test-nexcloud", external=True)


@nox.session(python=["3.9", "3.10", "3.11", "3.12", "3.13"], reuse_venv=True)
def test(session):
    session.install("pytest")
    session.run(
        "pytest",
        "--doctest-modules",
        "flozz_daily_mix",
    )
