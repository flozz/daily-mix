Things to do while releasing a new version
==========================================

This file is a memo for the maintainer.


1. Release
----------

* Update version number in ``setup.py``
* Update version number in ``flozz_daily_mix/__init__.py``
* Edit / update changelog in ``README.rst``
* Commit / tag (``git commit -m vX.Y.Z && git tag vX.Y.Z && git push && git push --tags``)


2. Publish PyPI package
-----------------------

Publish source dist and wheels on PyPI.

→ Automated :)


3. Publish Github Release
-------------------------

* Make a release on Github
* Add changelog
