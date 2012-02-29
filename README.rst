Python bindings to the OpenStack Glance API
=============================================

This is a client for the OpenStack Glance API. There's a Python API (the
``glanceclient`` module), and a command-line script (``glance``). The
Glance 2.0 API is still a moving target, so this module will remain in
"Beta" status until the API is finalized and fully implemented.

Development takes place via the usual OpenStack processes as outlined in
the `OpenStack wiki`_.  The master repository is on GitHub__.

__ http://wiki.openstack.org/HowToContribute
__ http://github.com/openstack/python-glanceclient

This code a fork of `Rackspace's python-novaclient`__ which is in turn a fork of
`Jacobian's python-cloudservers`__. The python-glanceclient is licensed under
the Apache License like the rest of OpenStack.

__ http://github.com/rackspace/python-novaclient
__ http://github.com/jacobian/python-cloudservers

.. contents:: Contents:
   :local:

Python API
----------

By way of a quick-start::

    # use v2.0 auth with http://example.com:5000/v2.0")
    >>> from glanceclient.v2_0 import client
    >>> glance = client.Client(username=USERNAME, password=PASSWORD, tenant_name=TENANT, auth_url=KEYSTONE_URL)
    >>> glance.images.list()
    >>> image = glance.images.create(name="My Test Image")
    >>> print image.status
    'queued'
    >>> image.upload(open('/tmp/myimage.iso', 'rb'))
    >>> print image.status
    'active'
    >>> image_file = image.image_file
    >>> with open('/tmp/copyimage.iso', 'wb') as f:
            for chunk in image_file:
                f.write(chunk)
    >>> image.delete()


Command-line API
----------------

Installing this package gets you a command-line tool, ``glance``, that you
can use to interact with Glance's Identity API.

You'll need to provide your OpenStack tenant, username and password. You can do this
with the ``tenant_name``, ``--username`` and ``--password`` params, but it's
easier to just set them as environment variables::

    export OS_TENANT_NAME=project
    export OS_USERNAME=user
    export OS_PASSWORD=pass

You will also need to define the authentication url with ``--auth_url`` and the
version of the API with ``--identity_api_version``.  Or set them as an environment
variables as well::

    export OS_AUTH_URL=http://example.com:5000/v2.0
    export OS_IDENTITY_API_VERSION=2.0

Since the Identity service that Glance uses can return multiple regional image
endpoints in the Service Catalog, you can specify the one you want with
``--region_name`` (or ``export OS_REGION_NAME``).
It defaults to the first in the list returned.

You'll find complete documentation on the shell by running
``glance help``::

    usage: glance [--username USERNAME] [--password PASSWORD]
                  [--tenant_name TENANT_NAME | --tenant_id TENANT_ID]
                  [--auth_url AUTH_URL] [--region_name REGION_NAME]
                  [--identity_api_version IDENTITY_API_VERSION]
                  <subcommand> ...

    Command-line interface to the OpenStack Identity API.

    Positional arguments:
      <subcommand>
        catalog             List all image services in service catalog
        image-create        Create new image
        image-delete        Delete image
        image-list          List images
        image-update        Update image's name and other properties
        image-upload        Upload an image file
        image-download      Download an image file
        help                Display help about this program or one of its
                            subcommands.

    Optional arguments:
      --username USERNAME   Defaults to env[OS_USERNAME]
      --password PASSWORD   Defaults to env[OS_PASSWORD]
      --tenant_name TENANT_NAME
                            Defaults to env[OS_TENANT_NAME]
      --tenant_id TENANT_ID
                            Defaults to env[OS_TENANT_ID]
      --auth_url AUTH_URL   Defaults to env[OS_AUTH_URL]
      --region_name REGION_NAME
                            Defaults to env[OS_REGION_NAME]
      --identity_api_version IDENTITY_API_VERSION
                            Defaults to env[OS_IDENTITY_API_VERSION] or 2.0

See "glance help COMMAND" for help on a specific command.
