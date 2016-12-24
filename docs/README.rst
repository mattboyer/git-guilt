.. image:: https://travis-ci.org/mattboyer/git-guilt.svg?branch=master
    :target: https://travis-ci.org/mattboyer/git-guilt

.. image:: https://coveralls.io/repos/mattboyer/git-guilt/badge.svg?branch=master
    :target: https://coveralls.io/r/mattboyer/git-guilt

.. image:: https://landscape.io/github/mattboyer/git-guilt/master/landscape.svg?style=flat
    :target: https://landscape.io/github/mattboyer/git-guilt/master
    :alt: Code Health

.. image:: https://img.shields.io/pypi/v/git-guilt.svg
    :target: https://pypi.python.org/pypi/git-guilt/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/format/git-guilt.svg
    :target: https://pypi.python.org/pypi/git-guilt/
    :alt: Download format

.. image:: https://img.shields.io/pypi/pyversions/git-guilt.svg
    :target: https://pypi.python.org/pypi/git-guilt/
    :alt: Supported Python versions

git-guilt
=========

``git-guilt`` is a custom tool written for the `Git <http://git-scm.com/>`_ Source Code Management system. It aims to provide information regarding the *transfer* of ownership between two revisions of a repository. Think of it as a first-order derivative of `git-blame <http://git-scm.com/docs/git-blame>`_!

``git-guilt`` is a Python port of Tim Pettersen's JavaScript `tool <https://bitbucket.org/tpettersen/git-guilt>`_ of the same name.

Screenshot
----------

.. image:: docs/screenshot.png

Installation
------------

``git-guilt`` does not require any dependency beside Python and Git (and `argparse <https://pypi.python.org/pypi/argparse>`_ in case your version of Python doesn't include it). To install, simply type:

.. code-block:: bash

    $ pip install git-guilt

Why use git-guilt?
------------------

- ``git-guilt`` can be used to identify code reviewers. Authors whose overall ownership of the repository *decreases* for a given commit will often have valuable feedback to provide during a code review. Yesterday's design decisions may still be relevant today. And even if they're not, this is a great opportunity to learn from past mistakes!

- Likewise, ``git-guilt`` can be used to run periodic audits on the ownership of code in a repo. Middle managers love this stuff!

Documentation and usage
-----------------------

Please `read the docs <http://git-guilt.readthedocs.org/en/latest/git-guilt.1.html>`_.

Hacking git-guilt
-----------------

Once you've `cloned <https://help.github.com/articles/cloning-a-repository/>`_ this repository, be sure to install the build-time dependencies and you'll be ready to starting hacking away on your working copy. Please use `tox <https://tox.readthedocs.io/en/latest/>`_ as your one-stop shop to ensure that all code checks and tests pass on both Python 2 and Python 3  - it's what the continuous integration hook requires for pull requests.

.. code-block:: bash

    $ pip install -r requirements.txt
    $ tox

Notes
-----

Unit tests and integration tests are run for every commit. ``git-guilt`` is `tested <https://travis-ci.org/mattboyer/git-guilt>`_ on Python 2.7, and 3.5.

``git-guilt`` tries to be Unicode-friendly. There are tests for non-Latin character support in author names, repository paths and terminal output.

To-Dos
------

``git-guilt`` has only been tested on Linux so far. I expect some work to be needed to port terminal handling code to macOS. Support for Microsoft Windows would likely require more work.
