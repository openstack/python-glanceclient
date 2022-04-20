==============================
:program:`glance` CLI man page
==============================

.. program:: glance
.. highlight:: bash

SYNOPSIS
========

:program:`glance` [options] <command> [command-options]

:program:`glance help`

:program:`glance help` <command>


DESCRIPTION
===========

The :program:`glance` command line utility interacts with OpenStack Images
Service (Glance).

In order to use the CLI, you must provide your OpenStack username, password,
project (historically called tenant), and auth endpoint. You can use
configuration options ``--os-username``, ``--os-password``, ``--os-project-id``,
and ``--os-auth-url`` or set corresponding environment variables::

    export OS_USERNAME=user
    export OS_PASSWORD=pass
    export OS_PROJECT_ID=b363706f891f48019483f8bd6503c54b
    export OS_AUTH_URL=http://auth.example.com:5000/v2.0

The command line tool will attempt to reauthenticate using provided credentials
for every request. You can override this behavior by manually supplying an auth
token using ``--os-image-url`` and ``--os-auth-token`` or by setting
corresponding environment variables::

    export OS_IMAGE_URL=http://glance.example.org:9292/
    export OS_AUTH_TOKEN=3bcc3d3a03f44e3d8377f9247b0ad155

You can select an API version to use by ``--os-image-api-version`` option or by
setting corresponding environment variable::

    export OS_IMAGE_API_VERSION=1

Default Images API used is v2.

OPTIONS
=======

To get a list of available commands and options run::

    glance help

To get usage and options of a command::

    glance help <command>


EXAMPLES
========

Get information about image-create command::

    glance help image-create

See available images::

    glance image-list

To get a verbose output including more fields in the image list response::

    glance --verbose image-list

Create new image::

    glance image-create --name foo --disk-format=qcow2 \
                        --container-format=bare --visibility=public \
                        --file /tmp/foo.img

Describe a specific image::

    glance image-show <Image-ID>


BUGS
====

Glance client is hosted in Launchpad so you can view current bugs at
https://bugs.launchpad.net/python-glanceclient/.
