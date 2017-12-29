==========================
 Python Library Reference
==========================

In order to use the python api directly, you must first obtain an auth
token and identify which endpoint you wish to speak to. Once you have
done so, you can use the API like so::

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
            for chunk in image.data():
                f.write(chunk)
    >>> image.delete()

.. toctree::
   :maxdepth: 2

   Python API Reference <api/modules>
   apiv2
