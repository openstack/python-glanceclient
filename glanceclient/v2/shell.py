# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from glanceclient.common import progressbar
from glanceclient.common import utils
from glanceclient import exc
import json
import os
from os.path import expanduser

IMAGE_SCHEMA = None


def get_image_schema():
    global IMAGE_SCHEMA
    if IMAGE_SCHEMA is None:
        schema_path = expanduser("~/.glanceclient/image_schema.json")
        if os.path.exists(schema_path) and os.path.isfile(schema_path):
            with file(schema_path, "r") as f:
                schema_raw = f.read()
                IMAGE_SCHEMA = json.loads(schema_raw)
    return IMAGE_SCHEMA


@utils.schema_args(get_image_schema)
@utils.arg('--property', metavar="<key=value>", action='append',
           default=[], help=('Arbitrary property to associate with image.'
                             ' May be used multiple times.'))
def do_image_create(gc, args):
    """Create a new image."""
    schema = gc.schemas.get("image")
    _args = [(x[0].replace('-', '_'), x[1]) for x in vars(args).items()]
    fields = dict(filter(lambda x: x[1] is not None and
                         (x[0] == 'property' or
                          schema.is_core_property(x[0])),
                         _args))

    raw_properties = fields.pop('property', [])
    for datum in raw_properties:
        key, value = datum.split('=', 1)
        fields[key] = value

    image = gc.images.create(**fields)
    ignore = ['self', 'access', 'file', 'schema']
    image = dict([item for item in image.iteritems()
                  if item[0] not in ignore])
    utils.print_dict(image)


@utils.arg('id', metavar='<IMAGE_ID>', help='ID of image to update.')
@utils.schema_args(get_image_schema, omit=['id'])
@utils.arg('--property', metavar="<key=value>", action='append',
           default=[], help=('Arbitrary property to associate with image.'
                             ' May be used multiple times.'))
@utils.arg('--remove-property', metavar="key", action='append', default=[],
           help="Name of arbitrary property to remove from the image")
def do_image_update(gc, args):
    """Update an existing image."""
    schema = gc.schemas.get("image")
    _args = [(x[0].replace('-', '_'), x[1]) for x in vars(args).items()]
    fields = dict(filter(lambda x: x[1] is not None and
                         (x[0] in ['property', 'remove_property'] or
                          schema.is_core_property(x[0])),
                         _args))

    raw_properties = fields.pop('property', [])
    for datum in raw_properties:
        key, value = datum.split('=', 1)
        fields[key] = value

    remove_properties = fields.pop('remove_property', None)

    image_id = fields.pop('id')
    image = gc.images.update(image_id, remove_properties, **fields)
    ignore = ['self', 'access', 'file', 'schema']
    image = dict([item for item in image.iteritems()
                  if item[0] not in ignore])
    utils.print_dict(image)


@utils.arg('--page-size', metavar='<SIZE>', default=None, type=int,
           help='Number of images to request in each paginated request.')
@utils.arg('--visibility', metavar='<VISIBILITY>',
           help='The visibility of the images to display.')
@utils.arg('--member-status', metavar='<MEMBER_STATUS>',
           help='The status of images to display.')
@utils.arg('--owner', metavar='<OWNER>',
           help='Display images owned by <OWNER>.')
@utils.arg('--checksum', metavar='<CHECKSUM>',
           help='Display images matching the checksum')
@utils.arg('--tag', metavar='<TAG>', action='append',
           help="Filter images by an user-defined tag.")
def do_image_list(gc, args):
    """List images you can access."""
    filter_keys = ['visibility', 'member_status', 'owner', 'checksum', 'tag']
    filter_items = [(key, getattr(args, key)) for key in filter_keys]
    filters = dict([item for item in filter_items if item[1] is not None])

    kwargs = {'filters': filters}
    if args.page_size is not None:
        kwargs['page_size'] = args.page_size

    images = gc.images.list(**kwargs)
    columns = ['ID', 'Name']
    utils.print_list(images, columns)


@utils.arg('id', metavar='<IMAGE_ID>', help='ID of image to describe.')
def do_image_show(gc, args):
    """Describe a specific image."""
    image = gc.images.get(args.id)
    ignore = ['self', 'access', 'file', 'schema']
    image = dict([item for item in image.iteritems() if item[0] not in ignore])
    utils.print_dict(image)


@utils.arg('--image-id', metavar='<IMAGE_ID>', required=True,
           help='Image to display members of.')
def do_member_list(gc, args):
    """Describe sharing permissions by image."""

    members = gc.image_members.list(args.image_id)
    columns = ['Image ID', 'Member ID', 'Status']
    utils.print_list(members, columns)


@utils.arg('image_id', metavar='<IMAGE_ID>',
           help='Image from which to remove member')
@utils.arg('member_id', metavar='<MEMBER_ID>',
           help='Tenant to remove as member')
def do_member_delete(gc, args):
    """Delete image member"""
    if not (args.image_id and args.member_id):
        utils.exit('Unable to delete member. Specify image_id and member_id')
    else:
        gc.image_members.delete(args.image_id, args.member_id)


@utils.arg('image_id', metavar='<IMAGE_ID>',
           help='Image from which to update member')
@utils.arg('member_id', metavar='<MEMBER_ID>',
           help='Tenant to update')
@utils.arg('member_status', metavar='<MEMBER_STATUS>',
           help='Updated status of member')
def do_member_update(gc, args):
    """Update the status of a member for a given image."""
    if not (args.image_id and args.member_id and args.member_status):
        utils.exit('Unable to update member. Specify image_id, member_id and'
                   ' member_status')
    else:
        member = gc.image_members.update(args.image_id, args.member_id,
                                         args.member_status)
        member = [member]
        columns = ['Image ID', 'Member ID', 'Status']
        utils.print_list(member, columns)


@utils.arg('image_id', metavar='<IMAGE_ID>',
           help='Image on which to create member')
@utils.arg('member_id', metavar='<MEMBER_ID>',
           help='Tenant to add as member')
def do_member_create(gc, args):
    """Create member for a given image."""
    if not (args.image_id and args.member_id):
        utils.exit('Unable to create member. Specify image_id and member_id')
    else:
        member = gc.image_members.create(args.image_id, args.member_id)
        member = [member]
        columns = ['Image ID', 'Member ID', 'Status']
        utils.print_list(member, columns)


@utils.arg('model', metavar='<MODEL>', help='Name of model to describe.')
def do_explain(gc, args):
    """Describe a specific model."""
    try:
        schema = gc.schemas.get(args.model)
    except exc.HTTPNotFound:
        utils.exit('Unable to find requested model \'%s\'' % args.model)
    else:
        formatters = {'Attribute': lambda m: m.name}
        columns = ['Attribute', 'Description']
        utils.print_list(schema.properties, columns, formatters)


@utils.arg('--file', metavar='<FILE>',
           help='Local file to save downloaded image data to. '
                'If this is not specified the image data will be '
                'written to stdout.')
@utils.arg('id', metavar='<IMAGE_ID>', help='ID of image to download.')
@utils.arg('--progress', action='store_true', default=False,
           help='Show download progress bar.')
def do_image_download(gc, args):
    """Download a specific image."""
    body = gc.images.data(args.id)
    if args.progress:
        body = progressbar.VerboseIteratorWrapper(body, len(body))
    utils.save_image(body, args.file)


@utils.arg('--file', metavar='<FILE>',
           help=('Local file that contains disk image to be uploaded'
                 ' during creation. Alternatively, images can be passed'
                 ' to the client via stdin.'))
@utils.arg('id', metavar='<IMAGE_ID>',
           help='ID of image to upload data to.')
def do_image_upload(gc, args):
    """Upload data for a specific image."""
    image_data = utils.get_data_file(args)
    gc.images.upload(args.id, image_data)


@utils.arg('id', metavar='<IMAGE_ID>', help='ID of image to delete.')
def do_image_delete(gc, args):
    """Delete specified image."""
    gc.images.delete(args.id)


@utils.arg('image_id', metavar='<IMAGE_ID>',
           help='Image to be updated with the given tag')
@utils.arg('tag_value', metavar='<TAG_VALUE>',
           help='Value of the tag')
def do_image_tag_update(gc, args):
        """Update an image with the given tag."""
        if not (args.image_id and args.tag_value):
            utils.exit('Unable to update tag. Specify image_id and tag_value')
        else:
            gc.image_tags.update(args.image_id, args.tag_value)
            image = gc.images.get(args.image_id)
            image = [image]
            columns = ['ID', 'Tags']
            utils.print_list(image, columns)


@utils.arg('image_id', metavar='<IMAGE_ID>',
           help='Image whose tag to be deleted')
@utils.arg('tag_value', metavar='<TAG_VALUE>',
           help='Value of the tag')
def do_image_tag_delete(gc, args):
    """Delete the tag associated with the given image."""
    if not (args.image_id and args.tag_value):
        utils.exit('Unable to delete tag. Specify image_id and tag_value')
    else:
        gc.image_tags.delete(args.image_id, args.tag_value)
