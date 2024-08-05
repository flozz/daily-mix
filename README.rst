FLOZz Daily Mix
---------------

FLOZz Daily Mix generates thematic playlist like Spotify's Daily Mix from a Subsonic API.

This is currently a work in progress and it has only been tested against ownCloud / Nextcloud Music servers.


Requirements
------------

* Python >= 3.8


Contributing
------------

Questions
~~~~~~~~~

If you have any question, you can:

* `Open an issue <https://github.com/flozz/daily-mix/issues>`_ on GitHub
* `Ask on Discord <https://discord.gg/P77sWhuSs4>`_ (I am not always available to chat, but I try to answer to everyone)


Bugs
~~~~

Please `open an issue <https://github.com/flozz/daily-mix/issues>`_ on GitHub with as much information as possible if you found a bug:

* Your operating system / Linux distribution (and its version)
* How you installed the software
* All the logs and message outputted by the software
* etc.


Pull requests
~~~~~~~~~~~~~

Please consider `filing a bug <https://github.com/flozz/daily-mix/issues>`_ before starting to work on a new feature; it will allow us to discuss the best way to do it. It is obviously unnecessary if you just want to fix a typo or small errors in the code.

Please note that your code must follow the coding style defined by the `pep8 <https://pep8.org>`_ and pass tests. `Black <https://black.readthedocs.io/en/stable>`_ and `Flake8 <https://flake8.pycqa.org/en/latest>`_ are used on this project to enforce the coding style.


Run the tests
~~~~~~~~~~~~~

You must install `Nox <https://nox.thea.codes/>`__ first::

    pip3 install nox

Then you can check for lint error::

    nox --session lint

and run the tests::

    nox --session test

You can use following commands to run the tests only on a certain Python version (the corresponding Python interpreter must be installed on your machine)::

    nox --session test-3.8
    nox --session test-3.9
    nox --session test-3.10
    nox --session test-3.11
    nox --session test-3.12

You can also fix coding style errors automatically with::

    nox -s black_fix


Support this project
--------------------

Want to support this project?

* `☕️ Buy me a coffee <https://www.buymeacoffee.com/flozz>`__
* `💵️ Give me a tip on PayPal <https://www.paypal.me/0xflozz>`__
* `❤️ Sponsor me on GitHub <https://github.com/sponsors/flozz>`__


Changelog
---------

* **[NEXT]** (changes on ``master`` that have not been released yet):

  * feat: Get available musics from a Subsonic API (Nextcloud Music)
  * feat: Generate a playlist from the available musics
  * feat: Write the playlist to Subsonic API
