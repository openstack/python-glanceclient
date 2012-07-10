Python bindings to the OpenStack Image API
=============================================

This is a client library for Glance built on the OpenStack Images API. It provides a Python API (the ``glanceclient`` module) and a command-line tool (``glance``). This library fully supports the the v1 Images API, with support for the v2 API in progress.

Development takes place via the usual OpenStack processes as outlined in the `OpenStack wiki <http://wiki.openstack.org/HowToContribute>`_.  The master repository is on `GitHub <http://github.com/openstack/python-glanceclient>`_.

Python API
----------
In order to use the python api directly, you must first obtain an auth token and identify which endpoint you wish to speak to. Once you have done so, you can use the API like so::

    >>> from glanceclient import Client
    >>> glance = Client('1', endpoint=OS_IMAGE_ENDPOINT, token=OS_AUTH_TOKEN)
    >>> image = glance.images.create(name="My Test Image")
    >>> print image.status
    'queued'
    >>> image.update(data=open('/tmp/myimage.iso', 'rb'))
    >>> print image.status
    'active'
    >>> with open('/tmp/copyimage.iso', 'wb') as f:
            for chunk in image.data:
                f.write(chunk)
    >>> image.delete()


Command-line Tool
----------------
In order to use the CLI, you must provide your OpenStack username, password, tenant, and auth endpoint. Use the corresponding configuration options (``--os-username``, ``--os-password``, ``--os-tenant-id``, and ``--os-auth-url``) or set them in environment variables::

    export OS_USERNAME=user
    export OS_PASSWORD=pass
    export OS_TENANT_ID=b363706f891f48019483f8bd6503c54b
    export OS_AUTH_URL=http://auth.example.com:5000/v2.0

The command line tool will attempt to reauthenticate using your provided credentials for every request. You can override this behavior by manually supplying an auth token using ``--os-image-url`` and ``--os-auth-token``. You can alternatively set these environment variables::

    export OS_IMAGE_URL=http://glance.example.org:9292/
    export OS_AUTH_TOKEN=3bcc3d3a03f44e3d8377f9247b0ad155

Once you've configured your authentication parameters, you can run ``glance help`` to see a complete listing of available commands.
