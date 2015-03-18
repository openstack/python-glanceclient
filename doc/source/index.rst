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
    >>> image.update(properties=dict(my_custom_property='value'))
    >>> with open('/tmp/copyimage.iso', 'wb') as f:
            for chunk in image.data:
                f.write(chunk)
    >>> image.delete()

For an API v2 example see also :doc:`apiv2`.

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

See also :doc:`/man/glance`.

Release Notes
=============

0.17.0
------

* 1420707_: Updated help for v2 member-update api
* glance-sorting-enhancements_: Extend images CLI v2 with new sorting syntax
* glance-sorting-enhancements_: Add the ability to specify the sort dir for each key
* glance-sorting-enhancements_: Adds the ability to sort images with multiple keys
* 1306774_: Apply expected patch format when updating tags in v2.images
* 1429088_: v2: read limit for list from --limit in shell
* 1428797_: Fix leaking sockets after v2 list operation
* 1423939_: Fix leaking sockets after v1 list operation
* 1408033_: v2: Allow upload from stdin on image-create

.. _1420707: https://bugs.launchpad.net/python-glanceclient/+bug/1420707
.. _glance-sorting-enhancements: https://blueprints.launchpad.net/glance/+spec/glance-sorting-enhancements
.. _1306774: https://bugs.launchpad.net/python-glanceclient/+bug/1306774
.. _1429088: https://bugs.launchpad.net/python-glanceclient/+bug/1429088
.. _1428797: https://bugs.launchpad.net/python-glanceclient/+bug/1428797
.. _1423939: https://bugs.launchpad.net/python-glanceclient/+bug/1423939
.. _1408033: https://bugs.launchpad.net/python-glanceclient/+bug/1408033

0.16.1
------

* 1423165_: Fix sockets leaking for a subset of operations (show, delete and update)
* 1395084_: Show error when trying to upload image data to non-queued image
* 1398838_: Stop showing JSON and HTML in error messages returned from the glance service
* 1396550_: More reliably register connection pools in cases where urllib3 is both vendored and installed system-wide

.. _1423165: https://bugs.launchpad.net/python-glanceclient/+bug/1423165
.. _1395084: https://bugs.launchpad.net/python-glanceclient/+bug/1395084
.. _1398838: https://bugs.launchpad.net/python-glanceclient/+bug/1398838
.. _1396550: https://bugs.launchpad.net/python-glanceclient/+bug/1396550

0.16.0
------

* Add --limit option to the v2 list operation. This allows a user to limit the
  number of images requested from the glance server. Previously the client
  would always go through the entire list of images
* The CLI exit code on keyboard interrupt is now ``130``, changed from ``1``.

* 1370283_: The set of supported SSL ciphers is now reduced to a smaller and more secure subset
* 1384664_, 1402746_: Fix enabling the progress bar on download and upload when
  image data is piped into the client causing the client to crash
* 1415935_: NoneType header values are now ignored when encoding headers
* 1341777_: Requests which are streamed are now explicitly closed when the end
  of the stream has been reached
* 1394236_: The CLI is now strict about what it counts as a boolean, and exits
  with an error if a non-boolean value is used as input to a boolean option
* 1401197_: The CLI is now strict about valid inputs to ``--os-image-api-version``
* 1333119_: The CLI now raises a more useful error message when a user requests the deletion of an image which is already deleted
* 1384759_: Fix client erroring if ``--os-tenant-id`` and ``--os-tenant-name``
  are not defined
* 1228744_: Add globoff option to debug curl statements. This allows it to work with IPv6 addresses

.. _1370283: https://bugs.launchpad.net/python-glanceclient/+bug/1370283
.. _1384664: https://bugs.launchpad.net/python-glanceclient/+bug/1384664
.. _1402746: https://bugs.launchpad.net/python-glanceclient/+bug/1402746
.. _1415935: https://bugs.launchpad.net/python-glanceclient/+bug/1415935
.. _1394236: https://bugs.launchpad.net/python-glanceclient/+bug/1394236
.. _1401197: https://bugs.launchpad.net/python-glanceclient/+bug/1401197
.. _1384759: https://bugs.launchpad.net/python-glanceclient/+bug/1384759
.. _1228744: https://bugs.launchpad.net/python-glanceclient/+bug/1228744
.. _1333119: https://bugs.launchpad.net/python-glanceclient/+bug/1333119

0.15.0
------

* Stop requiring a version to create a Client instance. The ``version`` argument is
  now a keyword. If no ``version`` is specified and a versioned endpoint is
  supplied, glanceclient will use the endpoint's version. If the endpoint is
  unversioned and a value for ``version`` is not supplied, glanceclient falls
  back to v1. This change is backwards-compatible. Examples::

    >>> glanceclient.Client(version=1, endpoint='http://localhost:9292') # returns a v1 client
    >>> glanceclient.Client(endpoint='http://localhost:9292/v2') # returns a v2 client
    >>> glanceclient.Client(endpoint='http://localhost:9292') # returns a v1 client
    >>> glanceclient.Client(2, 'http://localhost:9292/v2') # old behavior is preserved

* Add bash completion to glance client. The new bash completion files are stored in ``tools/glance.bash_completion``
* Add tty password entry. This prompts for a password if neither ``--os-password`` nor ``OS_PASSWORD`` have been set
* Add the ``--property-filter`` option from the v1 client to v2 image-list. This allows you to do something similar to::

    $ glance --os-image-api-version 2 image-list --property-filter os_distro=NixOS

* 1324067_: Allow --file flag in v2 image-create. This selects a local disk image to upload during the creation of the image
* 1395841_: Output a useful error on an invalid ``--os-image-api-version`` argument
* 1394965_: Add ``identity_headers`` back into the request headers
* 1350802_: Remove read only options from v2 shell commands. The options omitted are

  - ``created_at``
  - ``updated_at``
  - ``file``
  - ``checksum``
  - ``virtual_size``
  - ``size``
  - ``status``
  - ``schema``
  - ``direct_url``

* 1381295_: Stop setting X-Auth-Token key in http session header if there is no token provided
* 1378844_: Fix ``--public`` being ignored on image-create
* 1367782_: Fix to ensure ``endpoint_type`` is used by ``_get_endpoint()``
* 1381816_: Support Pagination for namespace list
* 1401032_: Add support for enum types in the schema that accept ``None``

.. _1324067: https://bugs.launchpad.net/python-glanceclient/+bug/1324067
.. _1395841: https://bugs.launchpad.net/python-glanceclient/+bug/1395841
.. _1394965: https://bugs.launchpad.net/python-glanceclient/+bug/1394965
.. _1350802: https://bugs.launchpad.net/python-glanceclient/+bug/1350802
.. _1381295: https://bugs.launchpad.net/python-glanceclient/+bug/1381295
.. _1378844: https://bugs.launchpad.net/python-glanceclient/+bug/1378844
.. _1367782: https://bugs.launchpad.net/python-glanceclient/+bug/1367782
.. _1381816: https://bugs.launchpad.net/python-glanceclient/+bug/1381816
.. _1401032: https://bugs.launchpad.net/python-glanceclient/+bug/1401032


0.14.2
------

* Add support for Glance Tasks calls (task create, list all and show)
* 1362179_: Default to system CA bundle if no CA certificate is provided
* 1350251_, 1347150_, 1362766_: Don't replace the https handler in the poolmanager
* 1371559_: Skip non-base properties in patch method

.. _1362179: https://bugs.launchpad.net/python-glanceclient/+bug/1362179
.. _1350251: https://bugs.launchpad.net/python-glanceclient/+bug/1350251
.. _1347150: https://bugs.launchpad.net/python-glanceclient/+bug/1347150
.. _1362766: https://bugs.launchpad.net/python-glanceclient/+bug/1362766
.. _1371559: https://bugs.launchpad.net/python-glanceclient/+bug/1371559


0.14.1
------

* Print traceback to stderr if ``--debug`` is set
* Downgrade log message for http request failures
* Fix CLI image-update giving the wrong help on '--tags' parameter
* 1367326_: Fix requests to non-bleeding edge servers using the v2 API
* 1329301_: Update how tokens are redacted
* 1369756_: Fix decoding errors when logging response headers

.. _1367326: https://bugs.launchpad.net/python-glanceclient/+bug/1367326
.. _1329301: https://bugs.launchpad.net/python-glanceclient/+bug/1329301
.. _1369756: https://bugs.launchpad.net/python-glanceclient/+bug/1369756


0.14.0
------

* Add support for metadata definitions catalog API
* Enable osprofiler profiling support to glanceclient and its shell. This adds the ``--profile <HMAC_KEY>`` argument.
* Add support for Keystone v3
* Replace old httpclient with requests
* Fix performance issue for image listing of v2 API
* 1364893_: Catch a new urllib3 exception: ProtocolError
* 1359880_: Fix error when logging http response with python 3
* 1357430_: Ensure server's SSL cert is validated to help guard against man-in-the-middle attack
* 1314218_: Remove deprecated commands from shell
* 1348030_: Fix glance-client on IPv6 controllers
* 1341777_: Don't stream non-binary requests

.. _1364893: https://bugs.launchpad.net/python-glanceclient/+bug/1364893
.. _1359880: https://bugs.launchpad.net/python-glanceclient/+bug/1359880
.. _1357430: https://bugs.launchpad.net/python-glanceclient/+bug/1357430
.. _1314218: https://bugs.launchpad.net/python-glanceclient/+bug/1314218
.. _1348030: https://bugs.launchpad.net/python-glanceclient/+bug/1348030
.. _1341777: https://bugs.launchpad.net/python-glanceclient/+bug/1341777


0.13.0
------

* Add command line support for image multi-locations
* Py3K support completed
* Fixed several issues related to UX
* Progress bar support for V2


0.12.0
------

* Add command line support for V2 image create, update, and upload
* Enable querying for images by tag
* 1230032_, 1231524_: Fix several issues with handling redirects
* 1206095_: Use openstack-images-v2.1-json-patch for update method

.. _1230032: http://bugs.launchpad.net/python-glanceclient/+bug/1230032
.. _1231524: http://bugs.launchpad.net/python-glanceclient/+bug/1231524
.. _1206095: http://bugs.launchpad.net/python-glanceclient/+bug/1206095

0.11.0
------

* 1212463_: Allow single-wildcard SSL common name matching
* 1208618_: Support absolute redirects for endpoint urls
* 1190606_: Properly handle integer-like image ids
* Support removing properties from images in the v2 library

.. _1212463: http://bugs.launchpad.net/python-glanceclient/+bug/1212463
.. _1208618: http://bugs.launchpad.net/python-glanceclient/+bug/1208618
.. _1190606: http://bugs.launchpad.net/python-glanceclient/+bug/1190606

0.10.0
------

* 1192229_: Security Update! Fix SSL certificate CNAME checking to handle ip addresses correctly
* Add an optional progress bar for image downloads
* Additional v2 api functionality, including image creation and uploads
* Allow v1 admin clients to list all users' images, and to list the images of specific tenants.
* Add a --checksum option to the v2 CLI for selecting images by checksum
* Added support for image creation and uploads to the v2 library
* Added support for updating and deleting v2 image tags to the v2 library and CLI
* Added support for managing image memberships to the v2 library and CLI
* Added a cli man page.
* 1184566_: Fix support for unix pipes when uploading images in the v1 CLI
* 1157864_: Fix an issue where glanceclient would fail with eventlet.

.. _1192229: http://bugs.launchpad.net/python-glanceclient/+bug/1192229
.. _1184566: http://bugs.launchpad.net/python-glanceclient/+bug/1184566
.. _1157864: http://bugs.launchpad.net/python-glanceclient/+bug/1157864

0.9.0
-----

* Implement 'visibility', 'owner' and 'member_status' filters for v2 CLI and library
* Relax prettytable dependency to v0.7.X
* 1118799_: Implement filter on 'is_public' attribute in v1 API
* 1157905_, 1130390_: Improve handling of SIGINT (CTRL-C)

.. _1118799: http://bugs.launchpad.net/python-glanceclient/+bug/1118799
.. _1157905: http://bugs.launchpad.net/python-glanceclient/+bug/1157905
.. _1130390: http://bugs.launchpad.net/python-glanceclient/+bug/1130390

0.8.0
-----

* Implement image-delete for Image API v2
* Update warlock dependency to >= 0.7.0 and < 1
* 1061150_: Support non-ASCII characters
* 1102944_: The port option is configurable when using HTTPS
* 1093380_: Support image names in place of IDs for CLI commands
* 1094917_: Better representation of errors through CLI

.. _1061150: http://bugs.launchpad.net/python-glanceclient/+bug/1061150
.. _1102944: http://bugs.launchpad.net/python-glanceclient/+bug/1102944
.. _1093380: http://bugs.launchpad.net/python-glanceclient/+bug/1093380
.. _1094917: http://bugs.launchpad.net/python-glanceclient/+bug/1094917

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
-----
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
