=====================================
python-glanceclient functional testing
=====================================

Idea
------

Run real client/server requests in the gate to catch issues which
are difficult to catch with a purely unit test approach.

Many projects (nova, keystone...) already have this form of testing in
the gate.


Testing Theory
----------------

Since python-glanceclient has two uses, CLI and python API, we should
have two sets of functional tests. CLI and python API. The python API
tests should never use the CLI. But the CLI tests can use the python API
where adding native support to the CLI for the required functionality
would involve a non trivial amount of work.


Functional Test Guidelines
---------------------------

* Consume credentials via standard client environmental variables::

    OS_USERNAME
    OS_PASSWORD
    OS_TENANT_NAME
    OS_AUTH_URL

* Try not to require an additional configuration file
