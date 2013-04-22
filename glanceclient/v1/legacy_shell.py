# Copyright 2012 OpenStack, LLC
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

"""
DEPRECATED functions that implement the same command line interface as the
legacy glance client.
"""

import argparse
import sys
import urlparse

from glanceclient.common import utils


SUCCESS = 0
FAILURE = 1


def get_image_fields_from_args(args):
    """
    Validate the set of arguments passed as field name/value pairs
    and return them as a mapping.
    """
    fields = {}
    for arg in args:
        pieces = arg.strip(',').split('=')
        if len(pieces) != 2:
            msg = ("Arguments should be in the form of field=value. "
                   "You specified %s." % arg)
            raise RuntimeError(msg)
        fields[pieces[0]] = pieces[1]

    return fields


def get_image_filters_from_args(args):
    """Build a dictionary of query filters based on the supplied args."""
    try:
        fields = get_image_fields_from_args(args)
    except RuntimeError, e:
        print e
        return FAILURE

    SUPPORTED_FILTERS = ['name', 'disk_format', 'container_format', 'status',
                         'min_ram', 'min_disk', 'size_min', 'size_max',
                         'changes-since']
    filters = {}
    for (key, value) in fields.items():
        if key not in SUPPORTED_FILTERS:
            key = 'property-%s' % (key,)
        filters[key] = value

    return filters


def print_image_formatted(client, image):
    """
    Formatted print of image metadata.

    :param client: The Glance client object
    :param image: The image metadata
    """
    uri_parts = urlparse.urlparse(client.endpoint)
    if uri_parts.port:
        hostbase = "%s:%s" % (uri_parts.hostname, uri_parts.port)
    else:
        hostbase = uri_parts.hostname
    print "URI: %s://%s/v1/images/%s" % (uri_parts.scheme, hostbase, image.id)
    print "Id: %s" % image.id
    print "Public: " + (image.is_public and "Yes" or "No")
    print "Protected: " + (image.protected and "Yes" or "No")
    print "Name: %s" % getattr(image, 'name', '')
    print "Status: %s" % image.status
    print "Size: %d" % int(image.size)
    print "Disk format: %s" % getattr(image, 'disk_format', '')
    print "Container format: %s" % getattr(image, 'container_format', '')
    print "Minimum Ram Required (MB): %s" % image.min_ram
    print "Minimum Disk Required (GB): %s" % image.min_disk
    if hasattr(image, 'owner'):
        print "Owner: %s" % image.owner
    if len(image.properties) > 0:
        for k, v in image.properties.items():
            print "Property '%s': %s" % (k, v)
    print "Created at: %s" % image.created_at
    if hasattr(image, 'deleted_at'):
        print "Deleted at: %s" % image.deleted_at
    if hasattr(image, 'updated_at'):
        print "Updated at: %s" % image.updated_at


@utils.arg('--silent-upload', action="store_true",
           help="DEPRECATED! Animations are always off.")
@utils.arg('fields', default=[], nargs='*', help=argparse.SUPPRESS)
def do_add(gc, args):
    """DEPRECATED! Use image-create instead."""
    try:
        fields = get_image_fields_from_args(args.fields)
    except RuntimeError, e:
        print e
        return FAILURE

    image_meta = {
        'is_public': utils.string_to_bool(
            fields.pop('is_public', 'False')),
        'protected': utils.string_to_bool(
            fields.pop('protected', 'False')),
        'min_disk': fields.pop('min_disk', 0),
        'min_ram': fields.pop('min_ram', 0),
    }

    #NOTE(bcwaldon): Use certain properties only if they are explicitly set
    optional = ['id', 'name', 'disk_format', 'container_format']
    for field in optional:
        if field in fields:
            image_meta[field] = fields.pop(field)

    # Strip any args that are not supported
    unsupported_fields = ['status', 'size']
    for field in unsupported_fields:
        if field in fields.keys():
            print 'Found non-settable field %s. Removing.' % field
            fields.pop(field)

    # We need either a location or image data/stream to add...
    image_data = None
    if 'location' in fields.keys():
        image_meta['location'] = fields.pop('location')
        if 'checksum' in fields.keys():
            image_meta['checksum'] = fields.pop('checksum')
    elif 'copy_from' in fields.keys():
        image_meta['copy_from'] = fields.pop('copy_from')
    else:
        # Grab the image data stream from stdin or redirect,
        # otherwise error out
        image_data = sys.stdin

    image_meta['data'] = image_data

    # allow owner to be set when image is created
    if 'owner' in fields.keys():
        image_meta['owner'] = fields.pop('owner')

    # Add custom attributes, which are all the arguments remaining
    image_meta['properties'] = fields

    if not args.dry_run:
        image = gc.images.create(**image_meta)
        print "Added new image with ID: %s" % image.id
        if args.verbose:
            print "Returned the following metadata for the new image:"
            for k, v in sorted(image.to_dict().items()):
                print " %(k)30s => %(v)s" % locals()
    else:
        print "Dry run. We would have done the following:"

        def _dump(dict):
            for k, v in sorted(dict.items()):
                print " %(k)30s => %(v)s" % locals()

        print "Add new image with metadata:"
        _dump(image_meta)

    return SUCCESS


@utils.arg('id', metavar='<IMAGE_ID>', help='ID of image to describe.')
@utils.arg('fields', default=[], nargs='*', help=argparse.SUPPRESS)
def do_update(gc, args):
    """DEPRECATED! Use image-update instead."""
    try:
        fields = get_image_fields_from_args(args.fields)
    except RuntimeError, e:
        print e
        return FAILURE

    image_meta = {}

    # Strip any args that are not supported
    nonmodifiable_fields = ['created_at', 'deleted_at', 'deleted',
                            'updated_at', 'size', 'status']
    for field in nonmodifiable_fields:
        if field in fields.keys():
            print 'Found non-modifiable field %s. Removing.' % field
            fields.pop(field)

    base_image_fields = ['disk_format', 'container_format', 'name',
                         'min_disk', 'min_ram', 'location', 'owner',
                         'copy_from']
    for field in base_image_fields:
        fvalue = fields.pop(field, None)
        if fvalue is not None:
            image_meta[field] = fvalue

    # Have to handle "boolean" values specially...
    if 'is_public' in fields:
        image_meta['is_public'] = utils.string_to_bool(fields.pop('is_public'))
    if 'protected' in fields:
        image_meta['protected'] = utils.string_to_bool(fields.pop('protected'))

    # Add custom attributes, which are all the arguments remaining
    image_meta['properties'] = fields

    if not args.dry_run:
        image = gc.images.update(args.id, **image_meta)
        print "Updated image %s" % args.id

        if args.verbose:
            print "Updated image metadata for image %s:" % args.id
            print_image_formatted(gc, image)
    else:
        def _dump(dict):
            for k, v in sorted(dict.items()):
                print " %(k)30s => %(v)s" % locals()

        print "Dry run. We would have done the following:"
        print "Update existing image with metadata:"
        _dump(image_meta)

    return SUCCESS


@utils.arg('id', metavar='<IMAGE_ID>', help='ID of image to describe.')
def do_delete(gc, args):
    """DEPRECATED! Use image-delete instead."""
    if not (args.force or
            user_confirm("Delete image %s?" % args.id, default=False)):
        print 'Not deleting image %s' % args.id
        return FAILURE

    gc.images.get(args.id).delete()


@utils.arg('id', metavar='<IMAGE_ID>', help='ID of image to describe.')
def do_show(gc, args):
    """DEPRECATED! Use image-show instead."""
    image = gc.images.get(args.id)
    print_image_formatted(gc, image)
    return SUCCESS


def _get_images(gc, args):
    parameters = {
        'filters': get_image_filters_from_args(args.filters),
        'page_size': args.limit,
    }

    optional_kwargs = ['marker', 'sort_key', 'sort_dir']
    for kwarg in optional_kwargs:
        value = getattr(args, kwarg, None)
        if value is not None:
            parameters[kwarg] = value

    return gc.images.list(**parameters)


@utils.arg('--limit', dest="limit", metavar="LIMIT", default=10,
           type=int, help="Page size to use while requesting image metadata")
@utils.arg('--marker', dest="marker", metavar="MARKER",
           default=None, help="Image index after which to begin pagination")
@utils.arg('--sort_key', dest="sort_key", metavar="KEY",
           help="Sort results by this image attribute.")
@utils.arg('--sort_dir', dest="sort_dir", metavar="[desc|asc]",
           help="Sort results in this direction.")
@utils.arg('filters', default=[], nargs='*', help=argparse.SUPPRESS)
def do_index(gc, args):
    """DEPRECATED! Use image-list instead."""
    images = _get_images(gc, args)

    if not images:
        return SUCCESS

    pretty_table = PrettyTable()
    pretty_table.add_column(36, label="ID")
    pretty_table.add_column(30, label="Name")
    pretty_table.add_column(20, label="Disk Format")
    pretty_table.add_column(20, label="Container Format")
    pretty_table.add_column(14, label="Size", just="r")

    print pretty_table.make_header()

    for image in images:
        print pretty_table.make_row(image.id,
                                    image.name,
                                    image.disk_format,
                                    image.container_format,
                                    image.size)


@utils.arg('--limit', dest="limit", metavar="LIMIT", default=10,
           type=int, help="Page size to use while requesting image metadata")
@utils.arg('--marker', dest="marker", metavar="MARKER",
           default=None, help="Image index after which to begin pagination")
@utils.arg('--sort_key', dest="sort_key", metavar="KEY",
           help="Sort results by this image attribute.")
@utils.arg('--sort_dir', dest="sort_dir", metavar="[desc|asc]",
           help="Sort results in this direction.")
@utils.arg('filters', default='', nargs='*', help=argparse.SUPPRESS)
def do_details(gc, args):
    """DEPRECATED! Use image-list instead."""
    images = _get_images(gc, args)
    for i, image in enumerate(images):
        if i == 0:
            print "=" * 80
        print_image_formatted(gc, image)
        print "=" * 80


def do_clear(gc, args):
    """DEPRECATED!"""
    if not (args.force or
            user_confirm("Delete all images?", default=False)):
        print 'Not deleting any images'
        return FAILURE

    images = gc.images.list()
    for image in images:
        if args.verbose:
            print 'Deleting image %s "%s" ...' % (image.id, image.name),
        try:
            image.delete()
            if args.verbose:
                print 'done'
        except Exception, e:
            print 'Failed to delete image %s' % image.id
            print e
            return FAILURE
    return SUCCESS


@utils.arg('image_id', help='Image ID to filters members with.')
def do_image_members(gc, args):
    """DEPRECATED! Use member-list instead."""
    members = gc.image_members.list(image=args.image_id)
    sharers = 0
    # Output the list of members
    for memb in members:
        can_share = ''
        if memb.can_share:
            can_share = ' *'
            sharers += 1
        print "%s%s" % (memb.member_id, can_share)

    # Emit a footnote
    if sharers > 0:
        print "\n(*: Can share image)"


@utils.arg('--can-share', default=False, action="store_true",
           help="Allow member to further share image.")
@utils.arg('member_id',
           help='ID of member (typically tenant) to grant access.')
def do_member_images(gc, args):
    """DEPRECATED! Use member-list instead."""
    members = gc.image_members.list(member=args.member_id)

    if not len(members):
        print "No images shared with member %s" % args.member_id
        return SUCCESS

    sharers = 0
    # Output the list of images
    for memb in members:
        can_share = ''
        if memb.can_share:
            can_share = ' *'
            sharers += 1
        print "%s%s" % (memb.image_id, can_share)

    # Emit a footnote
    if sharers > 0:
        print "\n(*: Can share image)"


@utils.arg('--can-share', default=False, action="store_true",
           help="Allow member to further share image.")
@utils.arg('image_id', help='ID of image to describe.')
@utils.arg('member_id',
           help='ID of member (typically tenant) to grant access.')
def do_members_replace(gc, args):
    """DEPRECATED!"""
    if not args.dry_run:
        for member in gc.image_members.list(image=args.image_id):
            gc.image_members.delete(args.image_id, member.member_id)
        gc.image_members.create(args.image_id, args.member_id, args.can_share)
    else:
        print "Dry run. We would have done the following:"
        print ('Replace members of image %s with "%s"'
               % (args.image_id, args.member_id))
        if args.can_share:
            print "New member would have been able to further share image."


@utils.arg('--can-share', default=False, action="store_true",
           help="Allow member to further share image.")
@utils.arg('image_id', help='ID of image to describe.')
@utils.arg('member_id',
           help='ID of member (typically tenant) to grant access.')
def do_member_add(gc, args):
    """DEPRECATED! Use member-create instead."""
    if not args.dry_run:
        gc.image_members.create(args.image_id, args.member_id, args.can_share)
    else:
        print "Dry run. We would have done the following:"
        print ('Add "%s" to membership of image %s' %
               (args.member_id, args.image_id))
        if args.can_share:
            print "New member would have been able to further share image."


def user_confirm(prompt, default=False):
    """
    Yes/No question dialog with user.

    :param prompt: question/statement to present to user (string)
    :param default: boolean value to return if empty string
                    is received as response to prompt

    """
    if default:
        prompt_default = "[Y/n]"
    else:
        prompt_default = "[y/N]"

    # for bug 884116, don't issue the prompt if stdin isn't a tty
    if not (hasattr(sys.stdin, 'isatty') and sys.stdin.isatty()):
        return default

    answer = raw_input("%s %s " % (prompt, prompt_default))

    if answer == "":
        return default
    else:
        return answer.lower() in ("yes", "y")


class PrettyTable(object):
    """Creates an ASCII art table

    Example:

        ID  Name              Size         Hits
        --- ----------------- ------------ -----
        122 image                       22     0
    """
    def __init__(self):
        self.columns = []

    def add_column(self, width, label="", just='l'):
        """Add a column to the table

        :param width: number of characters wide the column should be
        :param label: column heading
        :param just: justification for the column, 'l' for left,
                     'r' for right
        """
        self.columns.append((width, label, just))

    def make_header(self):
        label_parts = []
        break_parts = []
        for width, label, _ in self.columns:
            # NOTE(sirp): headers are always left justified
            label_part = self._clip_and_justify(label, width, 'l')
            label_parts.append(label_part)

            break_part = '-' * width
            break_parts.append(break_part)

        label_line = ' '.join(label_parts)
        break_line = ' '.join(break_parts)
        return '\n'.join([label_line, break_line])

    def make_row(self, *args):
        row = args
        row_parts = []
        for data, (width, _, just) in zip(row, self.columns):
            row_part = self._clip_and_justify(data, width, just)
            row_parts.append(row_part)

        row_line = ' '.join(row_parts)
        return row_line

    @staticmethod
    def _clip_and_justify(data, width, just):
        # clip field to column width
        clipped_data = str(data)[:width]

        if just == 'r':
            # right justify
            justified = clipped_data.rjust(width)
        else:
            # left justify
            justified = clipped_data.ljust(width)

        return justified
