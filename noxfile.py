import nox

PYTHON_FILES = [
    "flozz_daily_mix",
    "scripts",
    "noxfile.py",
    "setup.py",
]


@nox.session(reuse_venv=True)
def lint(session):
    session.install("flake8", "black")
    session.run("black", "--check", "--diff", "--color", *PYTHON_FILES)
    session.run("flake8", *PYTHON_FILES)


@nox.session(reuse_venv=True)
def black_fix(session):
    session.install("black")
    session.run("black", *PYTHON_FILES)


@nox.session(python=["3.8", "3.9", "3.10", "3.11", "3.12"], reuse_venv=True)
def test(session):
    session.install("pytest")
    session.run(
        "pytest",
        "--doctest-modules",
        "flozz_daily_mix",
    )
