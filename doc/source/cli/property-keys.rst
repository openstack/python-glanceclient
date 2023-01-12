===========================
Image service property keys
===========================

You can use the glanceclient command line interface to set image properties
that can be consumed by other services to affect the behavior of those other
services.

Properties can be set on an image at the time of image creation or they
can be set on an existing image.  Use the :command:`glance image-create`
and :command:`glance image-update` commands respectively.

For example:

.. code-block:: console

   $ glance image-update IMG-UUID --property architecture=x86_64

For a list of image properties that can be used to affect the behavior
of other services, refer to `Useful image properties
<https://docs.openstack.org/glance/latest/admin/useful-image-properties.html>`_
in the Glance Administration Guide.

.. note::

   Behavior set using image properties overrides behavior set using flavors.
   For more information, refer to `Manage images
   <https://docs.openstack.org/glance/latest/admin/manage-images.html>`_
   in the Glance Administration Guide.

.. note::

   Boolean properties expect one of the following values: '0', '1', 'f',
   'false', 'n', 'no', 'off', 'on', 't', 'true', 'y', 'yes' (case-insensitive).
