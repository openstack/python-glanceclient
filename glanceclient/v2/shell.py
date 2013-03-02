# Copyright 2012 OpenStack LLC.
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

from glanceclient.common import utils
from glanceclient import exc


@utils.arg('--page-size', metavar='<SIZE>', default=None, type=int,
           help='Number of images to request in each paginated request.')
@utils.arg('--visibility', metavar='<VISIBILITY>',
           help='The visibility of the images to display.')
@utils.arg('--member-status', metavar='<MEMBER_STATUS>',
           help='The status of images to display.')
@utils.arg('--owner', metavar='<OWNER>',
           help='Display images owned by <OWNER>.')
def do_image_list(gc, args):
    """List images you can access."""
    filter_keys = ['visibility', 'member_status', 'owner']
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
def do_image_download(gc, args):
    """Download a specific image."""
    body = gc.images.data(args.id)
    utils.save_image(body, args.file)


@utils.arg('id', metavar='<IMAGE_ID>', help='ID of image to delete.')
def do_image_delete(gc, args):
    """Delete specified image."""
    gc.images.delete(args.id)
