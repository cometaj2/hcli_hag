|pypi| |build status| |pyver|

HCLI hag
========

HCLI hag is a python package wrapper that contains an HCLI sample application (hag); hag is git's remote repo hosting companion; a WSGI host service and hcli to work with remote git repositories.

----

HCLI hag wraps hag (an HCLI) and is intended to be used with an HCLI Client [1] as presented via an HCLI Connector [2].

You can find out more about HCLI on hcli.io [3]

[1] https://github.com/cometaj2/huckle

[2] https://github.com/cometaj2/hcli_core

[3] http://hcli.io

Installation
------------

HCLI hag requires a supported version of Python and pip.

You'll need an HCLI Connector to run hag. For example, you can use HCLI Core (https://github.com/cometaj2/hcli_core), a WSGI server such as Green Unicorn (https://gunicorn.org/), and an HCLI Client like Huckle (https://github.com/cometaj2/huckle).


.. code-block:: console

    pip install hcli_hag
    pip install hcli_core
    pip install huckle
    pip install gunicorn
    hcli_core cli install `hcli_hag path`
    hcli_core cli config hag
    hcli_core cli config hag core.auth True
    hcli_core cli config hag hco.port 9000
    hcli_core cli config hag core.wsgiapp.port 10000
    hcli_core cli config hag core.wsgiapp.base.url http://localhost
    export HCLI_CORE_BOOTSTRAP_PASSWORD=admin
    hcli_core cli run hag | bash


Usage
-----

Open a different shell window.

Setup the huckle env eval in your .bash_profile (or other bash configuration) to avoid having to execute eval everytime you want to invoke HCLIs by name (e.g. hag).

Note that no CLI is actually installed by Huckle. Huckle reads the HCLI semantics exposed by the API via HCLI Connector and ends up behaving *like* the CLI it targets.

You can set a new user and credentials with the hco admin, per HCLI_CORE_BOOTSTRAP_PASSWORD credentials and then use that user authentication with hag

.. code-block:: console

    eval $(huckle env)
    huckle cli install localhost:8000
    huckle cli install localhost:9000
    huckle cli config hco
    huckle cli config hco auth.mode basic
    huckle cli config hco credential.helper keyring
    huckle cli credential hco admin <<< admin
    hco help
    hco ls
    hco useradd test
    hco passwd test <<< testing
    hco ls
    huckle cli config hag
    huckle cli config hag auth.mode basic
    huckle cli config hag credential.helper keyring
    huckle cli credential hag test <<< testing
    hag help
    hag ls


Versioning
----------

This project makes use of semantic versioning (http://semver.org) and may make use of the "devx",
"prealphax", "alphax" "betax", and "rcx" extensions where x is a number (e.g. 0.3.0-prealpha1)
on github.

Supports
--------

TBD

To Do
-----

- Add user identity length limit, reserved name (e.g. admin), and alpha-numeric constraints.

Bugs
----

TBD

.. |build status| image:: https://circleci.com/gh/cometaj2/hcli_hag.svg?style=shield
   :target: https://circleci.com/gh/cometaj2/hcli_hag
.. |pypi| image:: https://img.shields.io/pypi/v/hcli-hag?label=hcli-hag
   :target: https://pypi.org/project/hcli-hag
.. |pyver| image:: https://img.shields.io/pypi/pyversions/hcli-hag.svg
   :target: https://pypi.org/project/hcli-hag
