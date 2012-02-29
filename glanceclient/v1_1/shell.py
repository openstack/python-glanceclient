# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack LLC.
# Copyright 2011 Nebula, Inc.
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

from glanceclient.v1_1 import client
from glanceclient import utils

CLIENT_CLASS = client.Client


@utils.arg('tenant', metavar='<tenant-id>', nargs='?', default=None,
           help='Tenant ID (Optional);  lists all images if not specified')
def do_image_list(gc, args):
    """List images"""
    images = gc.images.list(tenant_id=args.tenant)
    utils.print_list(images, ['id', 'is_public', 'email', 'name'])


@utils.arg('--name', metavar='<image-name>', required=True,
           help='New image name (must be unique)')
@utils.arg('--is-public', metavar='<true|false>', default=True,
           help='Initial image is_public status (default true)')
def do_image_create(gc, args):
    """Create new image"""
    image = gc.images.create(args.name, args.passwd, args.email,
                           tenant_id=args.tenant_id, is_public=args.is_public)
    utils.print_dict(image._info)


@utils.arg('--name', metavar='<image-name>',
           help='Desired new image name')
@utils.arg('--is-public', metavar='<true|false>',
           help='Enable or disable image')
@utils.arg('id', metavar='<image-id>', help='Image ID to update')
def do_image_update(gc, args):
    """Update image's name, email, and is_public status"""
    kwargs = {}
    if args.name:
        kwargs['name'] = args.name
    if args.email:
        kwargs['email'] = args.email
    if args.is_public:
        kwargs['is_public'] = utils.string_to_bool(args.is_public)

    if not len(kwargs):
        print "User not updated, no arguments present."
        return

    try:
        gc.images.update(args.id, **kwargs)
        print 'User has been updated.'
    except Exception, e:
        print 'Unable to update image: %s' % e


@utils.arg('id', metavar='<image-id>', help='User ID to delete')
def do_image_delete(gc, args):
    """Delete image"""
    gc.images.delete(args.id)


def do_token_get(gc, args):
    """Display the current user's token"""
    utils.print_dict(gc.service_catalog.get_token())
