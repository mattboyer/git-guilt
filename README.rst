.. image:: https://travis-ci.org/mattboyer/py_git-guilt.svg?branch=master
   :target: https://travis-ci.org/mattboyer/py_git-guilt

.. image:: https://coveralls.io/repos/mattboyer/py_git-guilt/badge.svg?branch=master
   :target: https://coveralls.io/r/mattboyer/py_git-guilt?branch=master 

A Python port of Tim Pettersen's git-guilt
==========================================

``git-guilt`` aims to provide information regarding the *transfer* of ownership between two revisions of a repository.

Usage
-----

See docs

Installation
------------

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
