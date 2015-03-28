.. image:: https://travis-ci.org/mattboyer/git-guilt.svg?branch=master
    :target: https://travis-ci.org/mattboyer/git-guilt

.. image:: https://coveralls.io/repos/mattboyer/git-guilt/badge.svg?branch=master
    :target: https://coveralls.io/r/mattboyer/git-guilt

.. image:: https://pypip.in/version/git-guilt/badge.svg
    :target: https://pypi.python.org/pypi/git-guilt/
    :alt: Latest Version

.. image:: https://pypip.in/py_versions/git-guilt/badge.svg
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

To install, simply type:

.. code-block:: bash

    pip install git-guilt

You can also `clone <https://help.github.com/articles/cloning-a-repository/>`_ this repository and run the following from your working copy:

.. code-block:: bash

    python setup.py install

Why use git-guilt?
------------------

- ``git-guilt`` can be used to identify code reviewers. Authors whose overall ownership of the repository *decreases* for a given commit will often have valuable feedback to provide during a code review. Yesterday's design decisions may still be relevant today. And even if they're not, this is a great opportunity to learn from past mistakes!

- Likewise, ``git-guilt`` can be used to run periodic audits on the ownership of code in a repo. Middle managers love this stuff!

Documentation and usage
-----------------------

Please `read the docs <http://git-guilt.readthedocs.org>`_.

Notes
-----

Unit tests and integration tests are run for every commit. ``git-guilt`` is `tested <https://travis-ci.org/mattboyer/git-guilt>`_ on Python 2.6, 2.7, 3.3 and 3.4.

``git-guilt`` tries to be Unicode-friendly. There are tests for non-Latin character support in author names, repository paths and terminal output.

To-Dos
------

``git-guilt`` has only been tested on Linux so far. I expect some work to be needed to port terminal handling code to MacOS X. Support for Microsoft Windows would likely require more work.
