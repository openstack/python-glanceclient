Python API
==========
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
=================
In order to use the CLI, you must provide your OpenStack username, password, tenant, and auth endpoint. Use the corresponding configuration options (``--os-username``, ``--os-password``, ``--os-tenant-id``, and ``--os-auth-url``) or set them in environment variables::

    export OS_USERNAME=user
    export OS_PASSWORD=pass
    export OS_TENANT_ID=b363706f891f48019483f8bd6503c54b
    export OS_AUTH_URL=http://auth.example.com:5000/v2.0

The command line tool will attempt to reauthenticate using your provided credentials for every request. You can override this behavior by manually supplying an auth token using ``--os-image-url`` and ``--os-auth-token``. You can alternatively set these environment variables::

    export OS_IMAGE_URL=http://glance.example.org:9292/
    export OS_AUTH_TOKEN=3bcc3d3a03f44e3d8377f9247b0ad155

Once you've configured your authentication parameters, you can run ``glance help`` to see a complete listing of available commands.


Release Notes
=============

0.7.0
-----

* Add ``--store`` option to ``image-create`` command
* Deprecate ``--ca-file`` in favor of ``--os-cacert``
* 1082957_: Add ``--sort-key`` and ``--sort-dir`` CLI options to ``image-list`` command
* 1081542_: Change default ``image-list`` CLI sort to order by image name ascending
* 1079692_: Verify SSL certification hostnames when using HTTPS
* 1080739_: Use ``--os-region-name`` in service catalog lookup

.. _1082957: http://bugs.launchpad.net/python-glanceclient/+bug/1082957
.. _1081542: http://bugs.launchpad.net/python-glanceclient/+bug/1081542
.. _1079692: http://bugs.launchpad.net/python-glanceclient/+bug/1079692
.. _1080739: http://bugs.launchpad.net/python-glanceclient/+bug/1080739

0.6.0
-----

* Multiple image ID can be passed to ``glance image-delete``
* ``glance --version`` and glanceclient.__version__ expose the current library version
* Use ``--human-readable`` with ``image-list`` and ``image-show`` to display image sizes in human-friendly formats
* Use OpenSSL for HTTPS connections
* 1056220_: Always use 'Transfer-Encoding: chunked' when transferring image data
* 1052846_: Padded endpoints enabled (e.g. glance.example.com/padding/v1)
* 1050345_: ``glance image-create`` and ``glance image-update`` now work on Windows

.. _1056220: http://bugs.launchpad.net/python-glanceclient/+bug/1056220
.. _1052846: http://bugs.launchpad.net/python-glanceclient/+bug/1052846
.. _1050345: http://bugs.launchpad.net/python-glanceclient/+bug/1050345

0.5.1
----
* 1045824_: Always send Content-Length when updating image with image data
* 1046607_: Handle 300 Multiple Choices nicely in the CLI
* 1035931_: Properly display URI in legacy 'show' command
* 1048698_: Catch proper httplib InvalidURL exception

.. _1045824: http://bugs.launchpad.net/python-glanceclient/+bug/1045824
.. _1046607: http://bugs.launchpad.net/python-glanceclient/+bug/1046607
.. _1035931: http://bugs.launchpad.net/python-glanceclient/+bug/1035931
.. _1048698: http://bugs.launchpad.net/python-glanceclient/+bug/1048698

0.5.0
-----
* Add 'image-download' command to CLI
* Relax dependency on warlock to anything less than v2

0.4.2
-----
* 1037233_: Fix v1 image list where limit kwarg is less than page_size

.. _1037233: https://bugs.launchpad.net/python-glanceclient/+bug/1037233

0.4.1
-----
* Default to system CA cert if one is not provided while using SSL
* 1036315_: Allow 'deleted' to be provided in v1 API image update
* 1036299_: Fix case where boolean values were treated as strings in v1 API
* 1036297_: Fix case where int values were treated as strings in v1 API

.. _1036315: https://bugs.launchpad.net/python-glanceclient/+bug/1036315
.. _1036299: https://bugs.launchpad.net/python-glanceclient/+bug/1036299
.. _1036297: https://bugs.launchpad.net/python-glanceclient/+bug/1036297

0.4.0
-----
* Send client SSL certificate to server for self-identification
* Properly validate server SSL certificates
* Images API v2 image data download
