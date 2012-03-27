Python bindings to the OpenStack Image API
=============================================

This is a client for the Glance which uses the OpenStack Image API. There's a
Python API (the ``glanceclient`` module), and a command-line script (``glance``). 

Development takes place via the usual OpenStack processes as outlined in
the `OpenStack wiki`_.  The master repository is on GitHub__.

__ http://wiki.openstack.org/HowToContribute
__ http://github.com/openstack/python-glanceclient

This code is based on `OpenStack's python-keystoneclient`__ which is based on
`Rackspace's python-novaclient`__ which is in turn a fork of
`Jacobian's python-cloudservers`__. The python-glanceclient is licensed under
the Apache License like the rest of OpenStack.

__ http://github.com/openstack/python-keystoneclient
__ http://github.com/rackspace/python-novaclient
__ http://github.com/jacobian/python-cloudservers

.. contents:: Contents:
   :local:

Python API
----------

If you wish to use the internal python api directly, you must obtain an auth
token and identify which endpoint you wish to speak to manually. Once you have
done so, you can use the API::

    >>> from glanceclient.v1 import client
    >>> glance = client.Client(endpoint=OS_IMAGE_ENDPOINT, token=OS_AUTH_TOKEN)
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
can use to interact with Glance through the OpenStack Image API.

You'll need to provide your OpenStack username, password, tenant, and auth
endpoint. You can do this with the ``--os-tenant-id``, ``--os-username``,
``--os-password``, and ``--os-auth-url`` params, but it's easier to just set them
as environment variables::

    export OS_USERNAME=user
    export OS_PASSWORD=pass
    export OS_TENANT_ID=b363706f891f48019483f8bd6503c54b
    export OS_AUTH_URL=http://auth.example.com:5000/v2.0

Since the Identity service that Glance uses can return multiple regional image
endpoints in the Service Catalog, you can specify the one you want with
``--region_name`` (or ``export OS_REGION_NAME``).
It defaults to the first in the list returned.

If you already have an auth token and endpoint, you may manually pass them
in to skip automatic authentication with your identity service. Either define 
them in command-line flags (``--os-image-url`` and ``--os-auth-token``) or in 
environment variables::

    export OS_IMAGE_URL=http://glance.example.org:5000/v1
    export OS_AUTH_TOKEN=3bcc3d3a03f44e3d8377f9247b0ad155

You'll find complete documentation on the shell by running ``glance help``.
