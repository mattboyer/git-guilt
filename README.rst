.. image:: https://travis-ci.org/mattboyer/py_git-guilt.svg?branch=master
   :target: https://travis-ci.org/mattboyer/py_git-guilt

.. image:: https://coveralls.io/repos/mattboyer/py_git-guilt/badge.svg?branch=master
   :target: https://coveralls.io/r/mattboyer/py_git-guilt?branch=master 

git-guilt
=========

``git-guilt`` is a custom tool written for the `Git <http://git-scm.com/>`_ Source Code Management system. It aims to provide information regarding the *transfer* of ownership between two revisions of a repository. Think of it as a first-order derivative of `git-blame <http://git-scm.com/docs/git-blame>`_!

``git-guilt`` is a Python port of Tim Pettersen's JavaScript `tool <https://bitbucket.org/tpettersen/git-guilt>`_ of the same name.

Usage
-----

See docs

Installation
------------

To install, simply type:

.. code-block:: bash

    pip install git-guilt

You can also clone this repository and run the following from your working copy:

.. code-block:: bash

    python setup.py install

Why use git-guilt?
------------------

- ``git-guilt`` can be used to identify code reviewers. Authors whose overall ownership of the repository *decreases* for a given commit will often have valuable feedback to provide during a code review. Yesterday's design decisions may still be relevant today. And even if they're not, this is a great opportunity to learn from past mistakes!

- Likewise, ``git-guilt`` can be used to run periodic audits on the ownership of code in a repo. Middle managers love this stuff!

Examples
--------

.. code-block:: bash

    518-mboyer@marylou:~/tmp/koala [master:I=R=S_]$ git guilt HEAD~5 HEAD
    oklai             | 17 +++++++++++++++++
    Ethan             |  0
    Ziad Khoury Hanna |  0
    Ethan Lai         | -4 ----

Notes
-----

Unit tests and integration tests are run for every commit made to git-guilt. Continuous Integration services provided by Travis CI.

- Coverage metrics

- Unicode friendly
