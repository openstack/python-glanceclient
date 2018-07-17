Python API v2
=============

These Identity Service credentials can be used to authenticate::

    * auth_url: Identity Service endpoint for authorization
    * username: name of user
    * password: user's password
    * project_{name|id}: name or ID of project

Also the following parameters are required when using the Identity API v3::

    * user_domain_{name|id}: name or ID of a domain the user belongs to
    * project_domain_{name|id}: name or ID for a domain the project belongs to

To create a client::

   from keystoneauth1 import loading
   from keystoneauth1 import session
   from glanceclient import Client

   loader = loading.get_plugin_loader('password')
   auth = loader.load_from_options(
       auth_url=AUTH_URL,
       username=USERNAME,
       password=PASSWORD,
       project_id=PROJECT_ID)
   session = session.Session(auth=auth)

   glance = Client('2', session=session)


Create
------
Create a new image::

   image = glance.images.create(name="myNewImage")
   glance.images.upload(image.id, open('/tmp/myimage.iso', 'rb'))

Show
----
Describe a specific image::

   glance.images.get(image.id)

Update
------
Update a specific image::

   # update with a list of image attribute names and their new values
   glance.images.update(image.id, name="myNewImageName")

Custom Properties
-----------------
Set a custom property on an image::

   # set an arbitrary property on an image
   glance.images.update(image.id, my_custom_property='value')

Remove a custom property from an image::

   # remove the custom property 'my_custom_property'
   glance.images.update(image.id, remove_props=['my_custom_property'])

Delete
------
Delete specified image(s)::

   glance.images.delete(image.id)

List
----
List images you can access::

   for image in glance.images.list():
      print image

Download
--------
Download a specific image::

   d = glance.images.data(image.id)

Share an Image
--------------
Share a specific image with a tenant::

   glance.image_members.create(image_id, member_id)

Remove a Share
--------------
Remove a shared image from a tenant::

   glance.image_members.delete(image_id, member_id)

List Sharings
-------------
Describe sharing permissions by image or tenant::

   glance.image_members.list(image_id)

