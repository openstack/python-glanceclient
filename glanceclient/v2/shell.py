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

import json
import os
import sys

from oslo_utils import strutils

from glanceclient._i18n import _
from glanceclient.common import progressbar
from glanceclient.common import utils
from glanceclient import exc
from glanceclient.v2 import cache
from glanceclient.v2 import image_members
from glanceclient.v2 import image_schema
from glanceclient.v2 import images
from glanceclient.v2 import namespace_schema
from glanceclient.v2 import resource_type_schema
from glanceclient.v2 import tasks

MEMBER_STATUS_VALUES = image_members.MEMBER_STATUS_VALUES
IMAGE_SCHEMA = None
DATA_FIELDS = ('location', 'copy_from', 'file', 'uri')


def get_image_schema():
    global IMAGE_SCHEMA
    if IMAGE_SCHEMA is None:
        schema_path = os.path.expanduser("~/.glanceclient/image_schema.json")
        if os.path.isfile(schema_path):
            with open(schema_path, "r") as f:
                schema_raw = f.read()
                IMAGE_SCHEMA = json.loads(schema_raw)
        else:
            return image_schema._BASE_SCHEMA
    return IMAGE_SCHEMA


@utils.schema_args(get_image_schema, omit=['locations', 'os_hidden'])
# NOTE(rosmaita): to make this option more intuitive for end users, we
# do not use the Glance image property name 'os_hidden' here.  This means
# we must include 'os_hidden' in the 'omit' list above and handle the
# --hidden argument by hand
@utils.arg('--hidden', type=strutils.bool_from_string, metavar='[True|False]',
           default=None,
           dest='os_hidden',
           help=("If true, image will not appear in default image list "
                 "response."))
@utils.arg('--property', metavar="<key=value>", action='append',
           default=[], help=_('Arbitrary property to associate with image.'
                              ' May be used multiple times.'))
@utils.arg('--file', metavar='<FILE>',
           help=_('Local file that contains disk image to be uploaded '
                  'during creation. Alternatively, the image data can be '
                  'passed to the client via stdin.'))
@utils.arg('--progress', action='store_true', default=False,
           help=_('Show upload progress bar.'))
@utils.arg('--store', metavar='<STORE>',
           default=utils.env('OS_IMAGE_STORE', default=None),
           help='Backend store to upload image to.')
@utils.on_data_require_fields(DATA_FIELDS)
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

    backend = args.store

    file_name = fields.pop('file', None)
    using_stdin = hasattr(sys.stdin, 'isatty') and not sys.stdin.isatty()
    if args.store and not (file_name or using_stdin):
        utils.exit("--store option should only be provided with --file "
                   "option or stdin.")

    if backend:
        # determine if backend is valid
        _validate_backend(backend, gc)

    if file_name is not None and os.access(file_name, os.R_OK) is False:
        utils.exit("File %s does not exist or user does not have read "
                   "privileges to it" % file_name)
    image = gc.images.create(**fields)
    try:
        if utils.get_data_file(args) is not None:
            backend = fields.get('store', None)
            args.id = image['id']
            args.size = None
            do_image_upload(gc, args)
            image = gc.images.get(args.id)
    finally:
        utils.print_image(image)


@utils.schema_args(get_image_schema, omit=['locations', 'os_hidden'])
# NOTE: --hidden requires special handling; see note at do_image_create
@utils.arg('--hidden', type=strutils.bool_from_string, metavar='[True|False]',
           default=None,
           dest='os_hidden',
           help=("If true, image will not appear in default image list "
                 "response."))
@utils.arg('--property', metavar="<key=value>", action='append',
           default=[], help=_('Arbitrary property to associate with image.'
                              ' May be used multiple times.'))
@utils.arg('--file', metavar='<FILE>',
           help=_('Local file that contains disk image to be uploaded '
                  'during creation. Alternatively, the image data can be '
                  'passed to the client via stdin.'))
@utils.arg('--progress', action='store_true', default=False,
           help=_('Show upload progress bar.'))
@utils.arg('--import-method', metavar='<METHOD>',
           default=utils.env('OS_IMAGE_IMPORT_METHOD', default=None),
           help=_('Import method used for Image Import workflow. '
                  'Valid values can be retrieved with import-info command. '
                  'Defaults to env[OS_IMAGE_IMPORT_METHOD] or if that is '
                  'undefined uses \'glance-direct\' if data is provided using '
                  '--file or stdin. Otherwise, simply creates an image '
                  'record if no import-method and no data is supplied'))
@utils.arg('--uri', metavar='<IMAGE_URL>', default=None,
           help=_('URI to download the external image.'))
@utils.arg('--remote-region', metavar='<GLANCE_REGION>', default=None,
           help=_('REMOTE_GLANCE_REGION to download the image.'))
@utils.arg('--remote-image-id', metavar='<REMOTE_IMAGE_ID>', default=None,
           help=_('The IMAGE ID of the image of remote glance, which needs'
                  'to be imported with glance-download'))
@utils.arg('--remote-service-interface', metavar='<REMOTE_SERVICE_INTERFACE>',
           default='public',
           help=_('The Remote Glance Service Interface for glance-download'))
@utils.arg('--store', metavar='<STORE>',
           default=utils.env('OS_IMAGE_STORE', default=None),
           help='Backend store to upload image to.')
@utils.arg('--stores', metavar='<STORES>',
           default=utils.env('OS_IMAGE_STORES', default=None),
           help=_('Stores to upload image to if multi-stores import '
                  'available. Comma separated list. Available stores can be '
                  'listed with "stores-info" call.'))
@utils.arg('--all-stores', type=strutils.bool_from_string,
           metavar='[True|False]',
           default=None,
           dest='os_all_stores',
           help=_('"all-stores" can be ued instead of "stores"-list to '
                  'indicate that image should be imported into all available '
                  'stores.'))
@utils.arg('--allow-failure', type=strutils.bool_from_string,
           metavar='[True|False]',
           dest='os_allow_failure',
           default=utils.env('OS_IMAGE_ALLOW_FAILURE', default=True),
           help=_('Indicator if all stores listed (or available) must '
                  'succeed. "True" by default meaning that we allow some '
                  'stores to fail and the status can be monitored from the '
                  'image metadata. If this is set to "False" the import will '
                  'be reverted should any of the uploads fail. Only usable '
                  'with "stores" or "all-stores".'))
@utils.on_data_require_fields(DATA_FIELDS)
def do_image_create_via_import(gc, args):
    """EXPERIMENTAL: Create a new image via image import.

    Use the interoperable image import workflow to create an image.  This
    command is designed to be backward compatible with the current image-create
    command, so its behavior is as follows:

    * If an import-method is specified (either on the command line or through
      the OS_IMAGE_IMPORT_METHOD environment variable, then you must provide a
      data source appropriate to that method (for example, --file for
      glance-direct, or --uri for web-download).
    * If no import-method is specified AND you provide either a --file or
      data to stdin, the command will assume you are using the 'glance-direct'
      import-method and will act accordingly.
    * If no import-method is specified and no data is supplied via --file or
      stdin, the command will simply create an image record in 'queued' status.
    """
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

    file_name = fields.pop('file', None)
    using_stdin = hasattr(sys.stdin, 'isatty') and not sys.stdin.isatty()

    # special processing for backward compatibility with image-create
    if args.import_method is None and (file_name or using_stdin):
        args.import_method = 'glance-direct'

    if args.import_method == 'copy-image':
        utils.exit("Import method 'copy-image' cannot be used "
                   "while creating the image.")

    # determine whether the requested import method is valid
    import_methods = gc.images.get_import_info().get('import-methods')
    if args.import_method and args.import_method not in import_methods.get(
            'value'):
        utils.exit("Import method '%s' is not valid for this cloud. "
                   "Valid values can be retrieved with import-info command." %
                   args.import_method)

    # determine if backend is valid
    backend = None
    stores = getattr(args, "stores", None)
    all_stores = getattr(args, "os_all_stores", None)

    if (args.store and (stores or all_stores)) or (stores and all_stores):
        utils.exit("Only one of --store, --stores and --all-stores can be "
                   "provided")
    elif args.store:
        backend = args.store
        # determine if backend is valid
        _validate_backend(backend, gc)
    elif stores:
        # NOTE(jokke): Making sure here that we do not include the stores in
        # the create call
        fields.pop("stores")
        stores = str(stores).split(',')
        for store in stores:
            # determine if backend is valid
            _validate_backend(store, gc)

    # make sure we have all and only correct inputs for the requested method
    if args.import_method is None:
        if args.uri:
            utils.exit("You cannot use --uri without specifying an import "
                       "method.")
    if args.import_method == 'glance-direct':
        if backend and not (file_name or using_stdin):
            utils.exit("--store option should only be provided with --file "
                       "option or stdin for the glance-direct import method.")
        if stores and not (file_name or using_stdin):
            utils.exit("--stores option should only be provided with --file "
                       "option or stdin for the glance-direct import method.")
        if all_stores and not (file_name or using_stdin):
            utils.exit("--all-stores option should only be provided with "
                       "--file option or stdin for the glance-direct import "
                       "method.")

        if args.uri:
            utils.exit("You cannot specify a --uri with the glance-direct "
                       "import method.")
        if file_name is not None and os.access(file_name, os.R_OK) is False:
            utils.exit("File %s does not exist or user does not have read "
                       "privileges to it." % file_name)
        if file_name is not None and using_stdin:
            utils.exit("You cannot use both --file and stdin with the "
                       "glance-direct import method.")
        if not file_name and not using_stdin:
            utils.exit("You must specify a --file or provide data via stdin "
                       "for the glance-direct import method.")
    if args.import_method == 'web-download':
        if backend and not args.uri:
            utils.exit("--store option should only be provided with --uri "
                       "option for the web-download import method.")
        if stores and not args.uri:
            utils.exit("--stores option should only be provided with --uri "
                       "option for the web-download import method.")
        if all_stores and not args.uri:
            utils.exit("--all-stores option should only be provided with "
                       "--uri option for the web-download import method.")
        if not args.uri:
            utils.exit("URI is required for web-download import method. "
                       "Please use '--uri <uri>'.")
        if file_name:
            utils.exit("You cannot specify a --file with the web-download "
                       "import method.")
        if using_stdin:
            utils.exit("You cannot pass data via stdin with the web-download "
                       "import method.")

    if args.import_method == 'glance-download':
        if not (args.remote_region and args.remote_image_id):
            utils.exit("REMOTE GlANCE REGION and REMOTE IMAGE ID are "
                       "required for glance-download import method. "
                       "Please use --remote-region <region> and "
                       "--remote-image-id <remote-image-id>.")
        if args.uri:
            utils.exit("You cannot specify a --uri with the glance-download "
                       "import method.")
        if file_name:
            utils.exit("You cannot specify a --file with the glance-download "
                       "import method.")
        if using_stdin:
            utils.exit("You cannot pass data via stdin with the "
                       "glance-download import method.")

    # process
    image = gc.images.create(**fields)
    try:
        args.id = image['id']
        if args.import_method:
            if utils.get_data_file(args) is not None:
                args.size = None
                do_image_stage(gc, args)
            args.from_create = True
            args.stores = stores
            do_image_import(gc, args)
        image = gc.images.get(args.id)
    finally:
        utils.print_image(image)


def _validate_backend(backend, gc):
    try:
        enabled_backends = gc.images.get_stores_info().get('stores')
    except exc.HTTPNotFound:
        # NOTE(abhishekk): To maintain backward compatibility
        return

    if backend:
        valid_backend = False
        for available_backend in enabled_backends:
            if available_backend['id'] == backend:
                valid_backend = True
                break

        if not valid_backend:
            utils.exit("Store '%s' is not valid for this cloud. Valid "
                       "values can be retrieved with stores-info command." %
                       backend)


@utils.arg('id', metavar='<IMAGE_ID>', help=_('ID of image to update.'))
@utils.schema_args(get_image_schema, omit=['id', 'locations', 'tags',
                                           'os_hidden'])
# NOTE: --hidden requires special handling; see note at do_image_create
@utils.arg('--hidden', type=strutils.bool_from_string, metavar='[True|False]',
           default=None,
           dest='os_hidden',
           help=("If true, image will not appear in default image list "
                 "response."))
@utils.arg('--property', metavar="<key=value>", action='append',
           default=[], help=_('Arbitrary property to associate with image.'
                              ' May be used multiple times.'))
@utils.arg('--remove-property', metavar="key", action='append', default=[],
           help=_("Name of arbitrary property to remove from the image."))
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
    utils.print_image(image)


@utils.arg('--limit', metavar='<LIMIT>', default=None, type=int,
           help=_('Maximum number of images to get.'))
@utils.arg('--page-size', metavar='<SIZE>', default=None, type=int,
           help=_('Number of images to request in each paginated request.'))
@utils.arg('--visibility', metavar='<VISIBILITY>',
           help=_('The visibility of the images to display.'))
@utils.arg('--member-status', metavar='<MEMBER_STATUS>',
           help=_('The status of images to display.'))
@utils.arg('--owner', metavar='<OWNER>',
           help=_('Display images owned by <OWNER>.'))
@utils.arg('--property-filter', metavar='<KEY=VALUE>',
           help=_("Filter images by a user-defined image property."),
           action='append', dest='properties', default=[])
@utils.arg('--checksum', metavar='<CHECKSUM>',
           help=_('Displays images that match the MD5 checksum.'))
@utils.arg('--hash', dest='os_hash_value', default=None,
           metavar='<HASH_VALUE>',
           help=_('Displays images that match the specified hash value.'))
@utils.arg('--tag', metavar='<TAG>', action='append',
           help=_("Filter images by a user-defined tag."))
@utils.arg('--sort-key', default=[], action='append',
           choices=images.SORT_KEY_VALUES,
           help=_('Sort image list by specified fields.'
                  ' May be used multiple times.'))
@utils.arg('--sort-dir', default=[], action='append',
           choices=images.SORT_DIR_VALUES,
           help=_('Sort image list in specified directions.'))
@utils.arg('--sort', metavar='<key>[:<direction>]', default=None,
           help=(_("Comma-separated list of sort keys and directions in the "
                   "form of <key>[:<asc|desc>]. Valid keys: %s. OPTIONAL."
                   ) % ', '.join(images.SORT_KEY_VALUES)))
@utils.arg('--hidden',
           dest='os_hidden',
           metavar='[True|False]',
           default=None,
           type=strutils.bool_from_string,
           const=True,
           nargs='?',
           help="Filters results by hidden status. Default=None.")
@utils.arg('--include-stores',
           metavar='[True|False]',
           default=None,
           type=strutils.bool_from_string,
           const=True,
           nargs='?',
           help="Print backend store id.")
def do_image_list(gc, args):
    """List images you can access."""
    filter_keys = ['visibility', 'member_status', 'owner', 'checksum', 'tag',
                   'os_hidden', 'os_hash_value']
    filter_items = [(key, getattr(args, key)) for key in filter_keys]

    if args.properties:
        filter_properties = [prop.split('=', 1) for prop in args.properties]
        if any(len(pair) != 2 for pair in filter_properties):
            utils.exit('Argument --property-filter expected properties in the'
                       ' format KEY=VALUE')
        filter_items += filter_properties
    filters = dict([item for item in filter_items if item[1] is not None])

    kwargs = {'filters': filters}
    if args.limit is not None:
        kwargs['limit'] = args.limit
    if args.page_size is not None:
        kwargs['page_size'] = args.page_size

    if args.sort_key:
        kwargs['sort_key'] = args.sort_key
    if args.sort_dir:
        kwargs['sort_dir'] = args.sort_dir
    if args.sort is not None:
        kwargs['sort'] = args.sort
    elif not args.sort_dir and not args.sort_key:
        kwargs['sort_key'] = 'name'
        kwargs['sort_dir'] = 'asc'

    columns = ['ID', 'Name']

    if args.verbose:
        columns += ['Disk_format', 'Container_format', 'Size', 'Status',
                    'Owner']

    if args.include_stores:
        columns += ['Stores']

    images = gc.images.list(**kwargs)
    utils.print_list(images, columns)


@utils.arg('id', metavar='<IMAGE_ID>', help=_('ID of image to describe.'))
@utils.arg('--human-readable', action='store_true', default=False,
           help=_('Print image size in a human-friendly format.'))
@utils.arg('--max-column-width', metavar='<integer>', default=80,
           help=_('The max column width of the printed table.'))
def do_image_show(gc, args):
    """Describe a specific image."""
    image = gc.images.get(args.id)
    utils.print_image(image, args.human_readable, int(args.max_column_width))


@utils.arg('id', metavar='<IMAGE_ID>', help=_('ID of image to get tasks.'))
def do_image_tasks(gc, args):
    """Get tasks associated with image"""
    columns = ['Message', 'Status', 'Updated at']
    if args.verbose:
        columns_to_prepend = ['Image Id', 'Task Id']
        columns_to_extend = ['User Id', 'Request Id',
                             'Result', 'Owner', 'Input', 'Expires at']
        columns = columns_to_prepend + columns + columns_to_extend
    try:
        tasks = gc.images.get_associated_image_tasks(args.id)
        utils.print_dict_list(tasks['tasks'], columns)
    except exc.HTTPNotFound:
        utils.exit('Image %s not found.' % args.id)
    except exc.HTTPNotImplemented:
        utils.exit('Server does not support image tasks API (v2.12)')


def do_usage(gc, args):
    """Get quota usage information."""
    columns = ['Quota', 'Limit', 'Usage']
    usage = gc.info.get_usage()
    utils.print_dict_list(
        [dict(v, quota=k) for k, v in usage.items()],
        columns)


@utils.arg('--image-id', metavar='<IMAGE_ID>', required=True,
           help=_('Image to display members of.'))
def do_member_list(gc, args):
    """Describe sharing permissions by image."""
    members = gc.image_members.list(args.image_id)
    columns = ['Image ID', 'Member ID', 'Status']
    utils.print_list(members, columns)


@utils.arg('image_id', metavar='<IMAGE_ID>',
           help=_('Image from which to display member.'))
@utils.arg('member_id', metavar='<MEMBER_ID>',
           help=_('Project to display.'))
def do_member_get(gc, args):
    """Show details of an image member"""
    member = gc.image_members.get(args.image_id, args.member_id)
    utils.print_dict(member)


@utils.arg('image_id', metavar='<IMAGE_ID>',
           help=_('Image from which to remove member.'))
@utils.arg('member_id', metavar='<MEMBER_ID>',
           help=_('Tenant to remove as member.'))
def do_member_delete(gc, args):
    """Delete image member."""
    if not (args.image_id and args.member_id):
        utils.exit('Unable to delete member. Specify image_id and member_id')
    else:
        gc.image_members.delete(args.image_id, args.member_id)


@utils.arg('image_id', metavar='<IMAGE_ID>',
           help=_('Image from which to update member.'))
@utils.arg('member_id', metavar='<MEMBER_ID>',
           help=_('Tenant to update.'))
@utils.arg('member_status', metavar='<MEMBER_STATUS>',
           choices=MEMBER_STATUS_VALUES,
           help=(_('Updated status of member. Valid Values: %s') %
                 ', '.join(str(val) for val in MEMBER_STATUS_VALUES)))
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
           help=_('Image with which to create member.'))
@utils.arg('member_id', metavar='<MEMBER_ID>',
           help=_('Tenant to add as member.'))
def do_member_create(gc, args):
    """Create member for a given image."""
    if not (args.image_id and args.member_id):
        utils.exit('Unable to create member. Specify image_id and member_id')
    else:
        member = gc.image_members.create(args.image_id, args.member_id)
        member = [member]
        columns = ['Image ID', 'Member ID', 'Status']
        utils.print_list(member, columns)


@utils.arg('model', metavar='<MODEL>', help=_('Name of model to describe.'))
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


def do_import_info(gc, args):
    """Print import methods available from Glance."""
    try:
        import_info = gc.images.get_import_info()
    except exc.HTTPNotFound:
        utils.exit('Target Glance does not support Image Import workflow')
    else:
        utils.print_dict(import_info)


@utils.arg('--detail', default=False, action='store_true',
           help='Shows details of stores. Admin only.')
def do_stores_info(gc, args):
    """Print available backends from Glance."""
    try:
        if args.detail:
            stores_info = gc.images.get_stores_info_detail()
        else:
            stores_info = gc.images.get_stores_info()
    except exc.HTTPNotFound:
        utils.exit('Multi Backend support is not enabled')
    else:
        utils.print_dict(stores_info)


@utils.arg('id', metavar='<IMAGE_ID>', help=_('ID of image to update.'))
@utils.arg('--store', metavar='<STORE_ID>', required=True,
           help=_('Store to delete image from.'))
def do_stores_delete(gc, args):
    """Delete image from specific store."""
    try:
        gc.images.delete_from_store(args.store, args.id)
    except exc.HTTPNotFound:
        utils.exit('Multi Backend support is not enabled or Image/store not '
                   'found.')
    except (exc.HTTPForbidden, exc.HTTPException) as e:
        msg = ("Unable to delete image '%s' from store '%s'. (%s)" % (
               args.id,
               args.store,
               e))
        utils.exit(msg)


@utils.arg('--allow-md5-fallback', action='store_true',
           default=utils.env('OS_IMAGE_ALLOW_MD5_FALLBACK', default=False),
           help=_('If os_hash_algo and os_hash_value properties are available '
                  'on the image, they will be used to validate the downloaded '
                  'image data. If the indicated secure hash algorithm is not '
                  'available on the client, the download will fail. Use this '
                  'flag to indicate that in such a case the legacy MD5 image '
                  'checksum should be used to validate the downloaded data. '
                  'You can also set the environment variable '
                  'OS_IMAGE_ALLOW_MD5_FALLBACK to any value to activate this '
                  'option.'))
@utils.arg('--file', metavar='<FILE>',
           help=_('Local file to save downloaded image data to. '
                  'If this is not specified and there is no redirection '
                  'the image data will not be saved.'))
@utils.arg('id', metavar='<IMAGE_ID>', help=_('ID of image to download.'))
@utils.arg('--progress', action='store_true', default=False,
           help=_('Show download progress bar.'))
def do_image_download(gc, args):
    """Download a specific image."""
    if sys.stdout.isatty() and (args.file is None):
        msg = ('No redirection or local file specified for downloaded image '
               'data. Please specify a local file with --file to save '
               'downloaded image or redirect output to another source.')
        utils.exit(msg)

    try:
        body = gc.images.data(args.id,
                              allow_md5_fallback=args.allow_md5_fallback)
    except (exc.HTTPForbidden, exc.HTTPException) as e:
        msg = "Unable to download image '%s'. (%s)" % (args.id, e)
        utils.exit(msg)

    if body.wrapped is None:
        msg = ('Image %s has no data.' % args.id)
        utils.exit(msg)

    if args.progress:
        body = progressbar.VerboseIteratorWrapper(body, len(body))

    utils.save_image(body, args.file)


@utils.arg('--file', metavar='<FILE>',
           help=_('Local file that contains disk image to be uploaded.'
                  ' Alternatively, images can be passed'
                  ' to the client via stdin.'))
@utils.arg('--size', metavar='<IMAGE_SIZE>', type=int,
           help=_('Size in bytes of image to be uploaded. Default is to get '
                  'size from provided data object but this is supported in '
                  'case where size cannot be inferred.'),
           default=None)
@utils.arg('--progress', action='store_true', default=False,
           help=_('Show upload progress bar.'))
@utils.arg('id', metavar='<IMAGE_ID>',
           help=_('ID of image to upload data to.'))
@utils.arg('--store', metavar='<STORE>',
           default=utils.env('OS_IMAGE_STORE', default=None),
           help='Backend store to upload image to.')
def do_image_upload(gc, args):
    """Upload data for a specific image."""
    backend = None
    if args.store:
        backend = args.store
        # determine if backend is valid
        _validate_backend(backend, gc)

    image_data = utils.get_data_file(args)
    if args.progress:
        filesize = utils.get_file_size(image_data)
        if filesize is not None:
            # NOTE(kragniz): do not show a progress bar if the size of the
            # input is unknown (most likely a piped input)
            image_data = progressbar.VerboseFileWrapper(image_data, filesize)
    gc.images.upload(args.id, image_data, args.size, backend=backend)


@utils.arg('--file', metavar='<FILE>',
           help=_('Local file that contains disk image to be uploaded.'
                  ' Alternatively, images can be passed'
                  ' to the client via stdin.'))
@utils.arg('--size', metavar='<IMAGE_SIZE>', type=int,
           help=_('Size in bytes of image to be uploaded. Default is to get '
                  'size from provided data object but this is supported in '
                  'case where size cannot be inferred.'),
           default=None)
@utils.arg('--progress', action='store_true', default=False,
           help=_('Show upload progress bar.'))
@utils.arg('id', metavar='<IMAGE_ID>',
           help=_('ID of image to upload data to.'))
def do_image_stage(gc, args):
    """Upload data for a specific image to staging."""
    image_data = utils.get_data_file(args)
    if args.progress:
        filesize = utils.get_file_size(image_data)
        if filesize is not None:
            # NOTE(kragniz): do not show a progress bar if the size of the
            # input is unknown (most likely a piped input)
            image_data = progressbar.VerboseFileWrapper(image_data, filesize)
    gc.images.stage(args.id, image_data, args.size)


@utils.arg('--import-method', metavar='<METHOD>', default='glance-direct',
           help=_('Import method used for Image Import workflow. '
                  'Valid values can be retrieved with import-info command '
                  'and the default "glance-direct" is used with '
                  '"image-stage".'))
@utils.arg('--uri', metavar='<IMAGE_URL>', default=None,
           help=_('URI to download the external image.'))
@utils.arg('--remote-region', metavar='<REMOTE_GLANCE_REGION>', default=None,
           help=_('REMOTE GLANCE REGION to download the image.'))
@utils.arg('--remote-image-id', metavar='<REMOTE_IMAGE_ID>', default=None,
           help=_('The IMAGE ID of the image of remote glance, which needs'
                  'to be imported with glance-download'))
@utils.arg('--remote-service-interface', metavar='<REMOTE_SERVICE_INTERFACE>',
           default='public',
           help=_('The Remote Glance Service Interface for glance-download'))
@utils.arg('id', metavar='<IMAGE_ID>',
           help=_('ID of image to import.'))
@utils.arg('--store', metavar='<STORE>',
           default=utils.env('OS_IMAGE_STORE', default=None),
           help='Backend store to upload image to.')
@utils.arg('--stores', metavar='<STORES>',
           default=utils.env('OS_IMAGE_STORES', default=None),
           help='Stores to upload image to if multi-stores import available.')
@utils.arg('--all-stores', type=strutils.bool_from_string,
           metavar='[True|False]',
           default=None,
           dest='os_all_stores',
           help=_('"all-stores" can be ued instead of "stores"-list to '
                  'indicate that image should be imported all available '
                  'stores.'))
@utils.arg('--allow-failure', type=strutils.bool_from_string,
           metavar='[True|False]',
           dest='os_allow_failure',
           default=utils.env('OS_IMAGE_ALLOW_FAILURE', default=True),
           help=_('Indicator if all stores listed (or available) must '
                  'succeed. "True" by default meaning that we allow some '
                  'stores to fail and the status can be monitored from the '
                  'image metadata. If this is set to "False" the import will '
                  'be reverted should any of the uploads fail. Only usable '
                  'with "stores" or "all-stores".'))
def do_image_import(gc, args):
    """Initiate the image import taskflow."""
    backend = getattr(args, "store", None)
    stores = getattr(args, "stores", None)
    all_stores = getattr(args, "os_all_stores", None)
    allow_failure = getattr(args, "os_allow_failure", True)
    uri = getattr(args, "uri", None)
    remote_region = getattr(args, "remote_region", None)
    remote_image_id = getattr(args, "remote_image_id", None)
    remote_service_interface = getattr(args, "remote_service_interface", None)

    if not getattr(args, 'from_create', False):
        if (args.store and (stores or all_stores)) or (stores and all_stores):
            utils.exit("Only one of --store, --stores and --all-stores can be "
                       "provided")
        elif args.store:
            backend = args.store
            # determine if backend is valid
            _validate_backend(backend, gc)
        elif stores:
            stores = str(stores).split(',')

        # determine if backend is valid
        if stores:
            for store in stores:
                _validate_backend(store, gc)

    if getattr(args, 'from_create', False):
        # this command is being called "internally" so we can skip
        # validation -- just do the import and get out of here
        gc.images.image_import(
            args.id, args.import_method, args.uri,
            remote_region=remote_region,
            remote_image_id=remote_image_id,
            remote_service_interface=remote_service_interface,
            backend=backend,
            stores=stores, all_stores=all_stores,
            allow_failure=allow_failure)
        return

    # do input validation
    try:
        import_methods = gc.images.get_import_info().get('import-methods')
    except exc.HTTPNotFound:
        utils.exit('Target Glance does not support Image Import workflow')

    if args.import_method not in import_methods.get('value'):
        utils.exit("Import method '%s' is not valid for this cloud. "
                   "Valid values can be retrieved with import-info command." %
                   args.import_method)

    if args.import_method == 'web-download' and not args.uri:
        utils.exit("Provide URI for web-download import method.")
    if args.uri and args.import_method != 'web-download':
        utils.exit("Import method should be 'web-download' if URI is "
                   "provided.")

    if args.import_method == 'glance-download' and \
            not (remote_region and remote_image_id):
        utils.exit("Provide REMOTE_IMAGE_ID and remote-region for "
                   "'glance-download' import method.")
    if remote_region and args.import_method != 'glance-download':
        utils.exit("Import method should be 'glance-download' if "
                   "REMOTE REGION is provided.")
    if remote_image_id and args.import_method != 'glance-download':
        utils.exit("Import method should be 'glance-download' if "
                   "REMOTE IMAGE ID is provided.")

    if args.import_method == 'copy-image' and not (stores or all_stores):
        utils.exit("Provide either --stores or --all-stores for "
                   "'copy-image' import method.")

    # check image properties
    image = gc.images.get(args.id)
    container_format = image.get('container_format')
    disk_format = image.get('disk_format')
    if not (container_format and disk_format):
        utils.exit("The 'container_format' and 'disk_format' properties "
                   "must be set on an image before it can be imported.")

    image_status = image.get('status')
    if args.import_method == 'glance-direct':
        if image_status != 'uploading':
            utils.exit("The 'glance-direct' import method can only be applied "
                       "to an image in status 'uploading'")
    if args.import_method == 'web-download':
        if image_status != 'queued':
            utils.exit("The 'web-download' import method can only be applied "
                       "to an image in status 'queued'")
    if args.import_method == 'copy-image':
        if image_status != 'active':
            utils.exit("The 'copy-image' import method can only be used on "
                       "an image with status 'active'.")

    # finally, do the import
    gc.images.image_import(args.id, args.import_method, uri=uri,
                           remote_region=remote_region,
                           remote_image_id=remote_image_id,
                           remote_service_interface=remote_service_interface,
                           backend=backend, stores=stores,
                           all_stores=all_stores, allow_failure=allow_failure)

    image = gc.images.get(args.id)
    utils.print_image(image)


@utils.arg('id', metavar='<IMAGE_ID>', nargs='+',
           help=_('ID of image(s) to delete.'))
def do_image_delete(gc, args):
    """Delete specified image."""
    failure_flag = False
    for args_id in args.id:
        try:
            gc.images.delete(args_id)
        except exc.HTTPForbidden:
            msg = "You are not permitted to delete the image '%s'." % args_id
            utils.print_err(msg)
            failure_flag = True
        except exc.HTTPNotFound:
            msg = "No image with an ID of '%s' exists." % args_id
            utils.print_err(msg)
            failure_flag = True
        except exc.HTTPConflict:
            msg = "Unable to delete image '%s' because it is in use." % args_id
            utils.print_err(msg)
            failure_flag = True
        except exc.HTTPException as e:
            msg = "'%s': Unable to delete image '%s'" % (e, args_id)
            utils.print_err(msg)
            failure_flag = True
    if failure_flag:
        utils.exit()


@utils.arg('id', metavar='<IMAGE_ID>',
           help=_('ID of image to deactivate.'))
def do_image_deactivate(gc, args):
    """Deactivate specified image."""
    gc.images.deactivate(args.id)


@utils.arg('id', metavar='<IMAGE_ID>',
           help=_('ID of image to reactivate.'))
def do_image_reactivate(gc, args):
    """Reactivate specified image."""
    gc.images.reactivate(args.id)


@utils.arg('image_id', metavar='<IMAGE_ID>',
           help=_('Image to be updated with the given tag.'))
@utils.arg('tag_value', metavar='<TAG_VALUE>',
           help=_('Value of the tag.'))
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
           help=_('ID of the image from which to delete tag.'))
@utils.arg('tag_value', metavar='<TAG_VALUE>',
           help=_('Value of the tag.'))
def do_image_tag_delete(gc, args):
    """Delete the tag associated with the given image."""
    if not (args.image_id and args.tag_value):
        utils.exit('Unable to delete tag. Specify image_id and tag_value')
    else:
        gc.image_tags.delete(args.image_id, args.tag_value)


@utils.arg('--url', metavar='<URL>', required=True,
           help=_('URL of location to add.'))
@utils.arg('--metadata', metavar='<STRING>', default='{}',
           help=_('Metadata associated with the location. '
                  'Must be a valid JSON object (default: %(default)s)'))
@utils.arg('--checksum', metavar='<STRING>',
           help=_('md5 checksum of image contents'))
@utils.arg('--hash-algo', metavar='<STRING>',
           help=_('Multihash algorithm'))
@utils.arg('--hash-value', metavar='<STRING>',
           help=_('Multihash value'))
@utils.arg('id', metavar='<IMAGE_ID>',
           help=_('ID of image to which the location is to be added.'))
def do_location_add(gc, args):
    """Add a location (and related metadata) to an image."""
    validation_data = {}
    if args.checksum:
        validation_data['checksum'] = args.checksum
    if args.hash_algo:
        validation_data['os_hash_algo'] = args.hash_algo
    if args.hash_value:
        validation_data['os_hash_value'] = args.hash_value
    try:
        metadata = json.loads(args.metadata)
    except ValueError:
        utils.exit('Metadata is not a valid JSON object.')
    else:
        image = gc.images.add_location(args.id, args.url, metadata,
                                       validation_data=validation_data)
        utils.print_dict(image)


@utils.arg('--url', metavar='<URL>', action='append', required=True,
           help=_('URL of location to remove. May be used multiple times.'))
@utils.arg('id', metavar='<IMAGE_ID>',
           help=_('ID of image whose locations are to be removed.'))
def do_location_delete(gc, args):
    """Remove locations (and related metadata) from an image."""
    gc.images.delete_locations(args.id, set(args.url))


@utils.arg('--url', metavar='<URL>', required=True,
           help=_('URL of location to update.'))
@utils.arg('--metadata', metavar='<STRING>', default='{}',
           help=_('Metadata associated with the location. '
                  'Must be a valid JSON object (default: %(default)s)'))
@utils.arg('id', metavar='<IMAGE_ID>',
           help=_('ID of image whose location is to be updated.'))
def do_location_update(gc, args):
    """Update metadata of an image's location."""
    try:
        metadata = json.loads(args.metadata)

        if metadata == {}:
            print("WARNING -- The location's metadata will be updated to "
                  "an empty JSON object.")
    except ValueError:
        utils.exit('Metadata is not a valid JSON object.')
    else:
        image = gc.images.update_location(args.id, args.url, metadata)
        utils.print_dict(image)


@utils.arg('--url', metavar='<URL>', required=True,
           help=_('URL of location to add.'))
@utils.arg('--validation-data', metavar='<STRING>', default='{}',
           help=_('Validation data containing os_hash_algo and os_hash_value '
                  'only associated to the image. Must be a valid JSON object '
                  '(default: %(default)s)'))
@utils.arg('id', metavar='<IMAGE_ID>',
           help=_('ID of image whose location is to be added.'))
def do_add_location(gc, args):
    """Add location to an image which is in `queued` state only. """
    try:
        invalid_val_data = None
        validation_data = json.loads(args.validation_data)
        accepted_values = ['os_hash_algo', 'os_hash_value']
        invalid_val_data = list(set(validation_data.keys()).difference(
            accepted_values))
        if invalid_val_data:
            utils.exit('Validation Data should contain only os_hash_algo '
                       'and os_hash_value. `%s` is not allowed' %
                       (*invalid_val_data,))

        allowed_hash_algo = ['sha512', 'sha256', 'sha1', 'md5']
        if validation_data and \
                validation_data['os_hash_algo'] not in allowed_hash_algo:
            raise utils.exit('os_hash_algo: `%s` is incorrect, '
                             'allowed hashing algorithms: %s' %
                             (validation_data['os_hash_algo'],
                              allowed_hash_algo))

    except ValueError:
        utils.exit('validation-data is not a valid JSON object.')
    else:
        image = gc.images.add_image_location(args.id, args.url,
                                             validation_data=validation_data)
        utils.print_image(image)


# Metadata - catalog
NAMESPACE_SCHEMA = None


def get_namespace_schema():
    global NAMESPACE_SCHEMA
    if NAMESPACE_SCHEMA is None:
        schema_path = os.path.expanduser("~/.glanceclient/"
                                         "namespace_schema.json")
        if os.path.isfile(schema_path):
            with open(schema_path, "r") as f:
                schema_raw = f.read()
                NAMESPACE_SCHEMA = json.loads(schema_raw)
        else:
            return namespace_schema.BASE_SCHEMA
    return NAMESPACE_SCHEMA


def _namespace_show(namespace, max_column_width=None):
    namespace = dict(namespace)  # Warlock objects are compatible with dicts
    # Flatten dicts for display
    if 'properties' in namespace:
        props = [k for k in namespace['properties']]
        namespace['properties'] = props
    if 'resource_type_associations' in namespace:
        assocs = [assoc['name']
                  for assoc in namespace['resource_type_associations']]
        namespace['resource_type_associations'] = assocs
    if 'objects' in namespace:
        objects = [obj['name'] for obj in namespace['objects']]
        namespace['objects'] = objects

    if 'tags' in namespace:
        tags = [tag['name'] for tag in namespace['tags']]
        namespace['tags'] = tags

    if max_column_width:
        utils.print_dict(namespace, max_column_width)
    else:
        utils.print_dict(namespace)


@utils.arg('namespace', metavar='<NAMESPACE>',
           help=_('Name of the namespace.'))
@utils.schema_args(get_namespace_schema, omit=['namespace', 'property_count',
                                               'properties', 'tag_count',
                                               'tags', 'object_count',
                                               'objects', 'resource_types'])
def do_md_namespace_create(gc, args):
    """Create a new metadata definitions namespace."""
    schema = gc.schemas.get('metadefs/namespace')
    _args = [(x[0].replace('-', '_'), x[1]) for x in vars(args).items()]
    fields = dict(filter(lambda x: x[1] is not None and
                         (schema.is_core_property(x[0])),
                         _args))
    namespace = gc.metadefs_namespace.create(**fields)

    _namespace_show(namespace)


@utils.arg('--file', metavar='<FILEPATH>',
           help=_('Path to file with namespace schema to import. '
                  'Alternatively, namespaces schema can be passed to the '
                  'client via stdin.'))
def do_md_namespace_import(gc, args):
    """Import a metadata definitions namespace from file or standard input."""
    namespace_data = utils.get_data_file(args)
    if not namespace_data:
        utils.exit('No metadata definition namespace passed via stdin or '
                   '--file argument.')

    try:
        namespace_json = json.load(namespace_data)
    except ValueError:
        utils.exit('Schema is not a valid JSON object.')
    else:
        namespace = gc.metadefs_namespace.create(**namespace_json)
        _namespace_show(namespace)


@utils.arg('id', metavar='<NAMESPACE>', help=_('Name of namespace to update.'))
@utils.schema_args(get_namespace_schema, omit=['property_count', 'properties',
                                               'tag_count', 'tags',
                                               'object_count', 'objects',
                                               'resource_type_associations'])
def do_md_namespace_update(gc, args):
    """Update an existing metadata definitions namespace."""
    schema = gc.schemas.get('metadefs/namespace')

    _args = [(x[0].replace('-', '_'), x[1]) for x in vars(args).items()]
    fields = dict(filter(lambda x: x[1] is not None and
                         (schema.is_core_property(x[0])),
                         _args))
    namespace = gc.metadefs_namespace.update(args.id, **fields)

    _namespace_show(namespace)


@utils.arg('namespace', metavar='<NAMESPACE>',
           help=_('Name of namespace to describe.'))
@utils.arg('--resource-type', metavar='<RESOURCE_TYPE>',
           help=_('Applies prefix of given resource type associated to a '
                  'namespace to all properties of a namespace.'), default=None)
@utils.arg('--max-column-width', metavar='<integer>', default=80,
           help=_('The max column width of the printed table.'))
def do_md_namespace_show(gc, args):
    """Describe a specific metadata definitions namespace.

    Lists also the namespace properties, objects and resource type
    associations.
    """
    kwargs = {}
    if args.resource_type:
        kwargs['resource_type'] = args.resource_type

    namespace = gc.metadefs_namespace.get(args.namespace, **kwargs)
    _namespace_show(namespace, int(args.max_column_width))


@utils.arg('--resource-types', metavar='<RESOURCE_TYPES>', action='append',
           help=_('Resource type to filter namespaces.'))
@utils.arg('--visibility', metavar='<VISIBILITY>',
           help=_('Visibility parameter to filter namespaces.'))
@utils.arg('--page-size', metavar='<SIZE>', default=None, type=int,
           help=_('Number of namespaces to request '
                  'in each paginated request.'))
def do_md_namespace_list(gc, args):
    """List metadata definitions namespaces."""
    filter_keys = ['resource_types', 'visibility']
    filter_items = [(key, getattr(args, key, None)) for key in filter_keys]
    filters = dict([item for item in filter_items if item[1] is not None])

    kwargs = {'filters': filters}
    if args.page_size is not None:
        kwargs['page_size'] = args.page_size

    namespaces = gc.metadefs_namespace.list(**kwargs)
    columns = ['namespace']
    utils.print_list(namespaces, columns)


@utils.arg('namespace', metavar='<NAMESPACE>',
           help=_('Name of namespace to delete.'))
def do_md_namespace_delete(gc, args):
    """Delete specified metadata definitions namespace with its contents."""
    gc.metadefs_namespace.delete(args.namespace)


# Metadata - catalog
RESOURCE_TYPE_SCHEMA = None


def get_resource_type_schema():
    global RESOURCE_TYPE_SCHEMA
    if RESOURCE_TYPE_SCHEMA is None:
        schema_path = os.path.expanduser("~/.glanceclient/"
                                         "resource_type_schema.json")
        if os.path.isfile(schema_path):
            with open(schema_path, "r") as f:
                schema_raw = f.read()
                RESOURCE_TYPE_SCHEMA = json.loads(schema_raw)
        else:
            return resource_type_schema.BASE_SCHEMA
    return RESOURCE_TYPE_SCHEMA


@utils.arg('namespace', metavar='<NAMESPACE>', help=_('Name of namespace.'))
@utils.schema_args(get_resource_type_schema)
def do_md_resource_type_associate(gc, args):
    """Associate resource type with a metadata definitions namespace."""
    schema = gc.schemas.get('metadefs/resource_type')
    _args = [(x[0].replace('-', '_'), x[1]) for x in vars(args).items()]
    fields = dict(filter(lambda x: x[1] is not None and
                         (schema.is_core_property(x[0])),
                         _args))
    resource_type = gc.metadefs_resource_type.associate(args.namespace,
                                                        **fields)
    utils.print_dict(resource_type)


@utils.arg('namespace', metavar='<NAMESPACE>', help=_('Name of namespace.'))
@utils.arg('resource_type', metavar='<RESOURCE_TYPE>',
           help=_('Name of resource type.'))
def do_md_resource_type_deassociate(gc, args):
    """Deassociate resource type with a metadata definitions namespace."""
    gc.metadefs_resource_type.deassociate(args.namespace, args.resource_type)


def do_md_resource_type_list(gc, args):
    """List available resource type names."""
    resource_types = gc.metadefs_resource_type.list()
    utils.print_list(resource_types, ['name'])


@utils.arg('namespace', metavar='<NAMESPACE>', help=_('Name of namespace.'))
def do_md_namespace_resource_type_list(gc, args):
    """List resource types associated to specific namespace."""
    resource_types = gc.metadefs_resource_type.get(args.namespace)
    utils.print_list(resource_types, ['name', 'prefix', 'properties_target'])


@utils.arg('namespace', metavar='<NAMESPACE>',
           help=_('Name of namespace the property will belong.'))
@utils.arg('--name', metavar='<NAME>', required=True,
           help=_('Internal name of a property.'))
@utils.arg('--title', metavar='<TITLE>', required=True,
           help=_('Property name displayed to the user.'))
@utils.arg('--schema', metavar='<SCHEMA>', required=True,
           help=_('Valid JSON schema of a property.'))
@utils.arg('--type', metavar='<TYPE>', required=True,
           help=_('Type of the property'))
def do_md_property_create(gc, args):
    """Create a new metadata definitions property inside a namespace."""
    try:
        schema = json.loads(args.schema)
    except ValueError:
        utils.exit('Schema is not a valid JSON object.')
    else:
        fields = {'name': args.name, 'title': args.title, 'type': args.type}
        fields.update(schema)
        new_property = gc.metadefs_property.create(args.namespace, **fields)
        utils.print_dict(new_property)


@utils.arg('namespace', metavar='<NAMESPACE>',
           help=_('Name of namespace the property belongs.'))
@utils.arg('property', metavar='<PROPERTY>', help=_('Name of a property.'))
@utils.arg('--name', metavar='<NAME>', default=None,
           help=_('New name of a property.'))
@utils.arg('--title', metavar='<TITLE>', default=None,
           help=_('Property name displayed to the user.'))
@utils.arg('--schema', metavar='<SCHEMA>', default=None,
           help=_('Valid JSON schema of a property.'))
def do_md_property_update(gc, args):
    """Update metadata definitions property inside a namespace."""
    fields = {}
    if args.name:
        fields['name'] = args.name
    if args.title:
        fields['title'] = args.title
    if args.schema:
        try:
            schema = json.loads(args.schema)
        except ValueError:
            utils.exit('Schema is not a valid JSON object.')
        else:
            fields.update(schema)

    new_property = gc.metadefs_property.update(args.namespace, args.property,
                                               **fields)
    utils.print_dict(new_property)


@utils.arg('namespace', metavar='<NAMESPACE>',
           help=_('Name of namespace the property belongs.'))
@utils.arg('property', metavar='<PROPERTY>', help=_('Name of a property.'))
@utils.arg('--max-column-width', metavar='<integer>', default=80,
           help=_('The max column width of the printed table.'))
def do_md_property_show(gc, args):
    """Describe a specific metadata definitions property inside a namespace."""
    prop = gc.metadefs_property.get(args.namespace, args.property)
    utils.print_dict(prop, int(args.max_column_width))


@utils.arg('namespace', metavar='<NAMESPACE>',
           help=_('Name of namespace the property belongs.'))
@utils.arg('property', metavar='<PROPERTY>', help=_('Name of a property.'))
def do_md_property_delete(gc, args):
    """Delete a specific metadata definitions property inside a namespace."""
    gc.metadefs_property.delete(args.namespace, args.property)


@utils.arg('namespace', metavar='<NAMESPACE>', help=_('Name of namespace.'))
def do_md_namespace_properties_delete(gc, args):
    """Delete all metadata definitions property inside a specific namespace."""
    gc.metadefs_property.delete_all(args.namespace)


@utils.arg('namespace', metavar='<NAMESPACE>', help=_('Name of namespace.'))
def do_md_property_list(gc, args):
    """List metadata definitions properties inside a specific namespace."""
    properties = gc.metadefs_property.list(args.namespace)
    columns = ['name', 'title', 'type']
    utils.print_list(properties, columns)


def _object_show(obj, max_column_width=None):
    obj = dict(obj)  # Warlock objects are compatible with dicts
    # Flatten dicts for display
    if 'properties' in obj:
        objects = [k for k in obj['properties']]
        obj['properties'] = objects

    if max_column_width:
        utils.print_dict(obj, max_column_width)
    else:
        utils.print_dict(obj)


@utils.arg('namespace', metavar='<NAMESPACE>',
           help=_('Name of namespace the object will belong.'))
@utils.arg('--name', metavar='<NAME>', required=True,
           help=_('Internal name of an object.'))
@utils.arg('--schema', metavar='<SCHEMA>', required=True,
           help=_('Valid JSON schema of an object.'))
def do_md_object_create(gc, args):
    """Create a new metadata definitions object inside a namespace."""
    try:
        schema = json.loads(args.schema)
    except ValueError:
        utils.exit('Schema is not a valid JSON object.')
    else:
        fields = {'name': args.name}
        fields.update(schema)
        new_object = gc.metadefs_object.create(args.namespace, **fields)
        _object_show(new_object)


@utils.arg('namespace', metavar='<NAMESPACE>',
           help=_('Name of namespace the object belongs.'))
@utils.arg('object', metavar='<OBJECT>', help=_('Name of an object.'))
@utils.arg('--name', metavar='<NAME>', default=None,
           help=_('New name of an object.'))
@utils.arg('--schema', metavar='<SCHEMA>', default=None,
           help=_('Valid JSON schema of an object.'))
def do_md_object_update(gc, args):
    """Update metadata definitions object inside a namespace."""
    fields = {}
    if args.name:
        fields['name'] = args.name
    if args.schema:
        try:
            schema = json.loads(args.schema)
        except ValueError:
            utils.exit('Schema is not a valid JSON object.')
        else:
            fields.update(schema)

    new_object = gc.metadefs_object.update(args.namespace, args.object,
                                           **fields)
    _object_show(new_object)


@utils.arg('namespace', metavar='<NAMESPACE>',
           help=_('Name of namespace the object belongs.'))
@utils.arg('object', metavar='<OBJECT>', help=_('Name of an object.'))
@utils.arg('--max-column-width', metavar='<integer>', default=80,
           help=_('The max column width of the printed table.'))
def do_md_object_show(gc, args):
    """Describe a specific metadata definitions object inside a namespace."""
    obj = gc.metadefs_object.get(args.namespace, args.object)
    _object_show(obj, int(args.max_column_width))


@utils.arg('namespace', metavar='<NAMESPACE>',
           help=_('Name of namespace the object belongs.'))
@utils.arg('object', metavar='<OBJECT>', help=_('Name of an object.'))
@utils.arg('property', metavar='<PROPERTY>', help=_('Name of a property.'))
@utils.arg('--max-column-width', metavar='<integer>', default=80,
           help=_('The max column width of the printed table.'))
def do_md_object_property_show(gc, args):
    """Describe a specific metadata definitions property inside an object."""
    obj = gc.metadefs_object.get(args.namespace, args.object)
    try:
        prop = obj['properties'][args.property]
        prop['name'] = args.property
    except KeyError:
        utils.exit('Property %s not found in object %s.' % (args.property,
                   args.object))
    utils.print_dict(prop, int(args.max_column_width))


@utils.arg('namespace', metavar='<NAMESPACE>',
           help=_('Name of namespace the object belongs.'))
@utils.arg('object', metavar='<OBJECT>', help=_('Name of an object.'))
def do_md_object_delete(gc, args):
    """Delete a specific metadata definitions object inside a namespace."""
    gc.metadefs_object.delete(args.namespace, args.object)


@utils.arg('namespace', metavar='<NAMESPACE>', help=_('Name of namespace.'))
def do_md_namespace_objects_delete(gc, args):
    """Delete all metadata definitions objects inside a specific namespace."""
    gc.metadefs_object.delete_all(args.namespace)


@utils.arg('namespace', metavar='<NAMESPACE>', help=_('Name of namespace.'))
def do_md_object_list(gc, args):
    """List metadata definitions objects inside a specific namespace."""
    objects = gc.metadefs_object.list(args.namespace)
    columns = ['name', 'description']
    column_settings = {
        "description": {
            "max_width": 50,
            "align": "l"
        }
    }
    utils.print_list(objects, columns, field_settings=column_settings)


def _tag_show(tag, max_column_width=None):
    tag = dict(tag)  # Warlock objects are compatible with dicts
    if max_column_width:
        utils.print_dict(tag, max_column_width)
    else:
        utils.print_dict(tag)


@utils.arg('namespace', metavar='<NAMESPACE>',
           help=_('Name of the namespace the tag will belong to.'))
@utils.arg('--name', metavar='<NAME>', required=True,
           help=_('The name of the new tag to add.'))
def do_md_tag_create(gc, args):
    """Add a new metadata definitions tag inside a namespace."""
    name = args.name.strip()
    if name:
        new_tag = gc.metadefs_tag.create(args.namespace, name)
        _tag_show(new_tag)
    else:
        utils.exit('Please supply at least one non-blank tag name.')


@utils.arg('namespace', metavar='<NAMESPACE>',
           help=_('Name of the namespace the tags will belong to.'))
@utils.arg('--names', metavar='<NAMES>', required=True,
           help=_('A comma separated list of tag names.'))
@utils.arg('--delim', metavar='<DELIM>', required=False,
           help=_('The delimiter used to separate the names'
                  ' (if none is provided then the default is a comma).'))
@utils.arg('--append', default=False, action='store_true', required=False,
           help=_('Append the new tags to the existing ones instead of'
                  'overwriting them'))
def do_md_tag_create_multiple(gc, args):
    """Create new metadata definitions tags inside a namespace."""
    delim = args.delim or ','
    tags = []
    names_list = args.names.split(delim)
    for name in names_list:
        name = name.strip()
        if name:
            tags.append(name)

    if not tags:
        utils.exit('Please supply at least one tag name. For example: '
                   '--names Tag1')

    fields = {'tags': tags, 'append': args.append}
    new_tags = gc.metadefs_tag.create_multiple(args.namespace, **fields)
    columns = ['name']
    column_settings = {
        "description": {
            "max_width": 50,
            "align": "l"
        }
    }
    utils.print_list(new_tags, columns, field_settings=column_settings)


@utils.arg('namespace', metavar='<NAMESPACE>',
           help=_('Name of the namespace to which the tag belongs.'))
@utils.arg('tag', metavar='<TAG>', help=_('Name of the old tag.'))
@utils.arg('--name', metavar='<NAME>', default=None, required=True,
           help=_('New name of the new tag.'))
def do_md_tag_update(gc, args):
    """Rename a metadata definitions tag inside a namespace."""
    name = args.name.strip()
    if name:
        fields = {'name': name}
        new_tag = gc.metadefs_tag.update(args.namespace, args.tag,
                                         **fields)
        _tag_show(new_tag)
    else:
        utils.exit('Please supply at least one non-blank tag name.')


@utils.arg('namespace', metavar='<NAMESPACE>',
           help=_('Name of the namespace to which the tag belongs.'))
@utils.arg('tag', metavar='<TAG>', help=_('Name of the tag.'))
def do_md_tag_show(gc, args):
    """Describe a specific metadata definitions tag inside a namespace."""
    tag = gc.metadefs_tag.get(args.namespace, args.tag)
    _tag_show(tag)


@utils.arg('namespace', metavar='<NAMESPACE>',
           help=_('Name of the namespace to which the tag belongs.'))
@utils.arg('tag', metavar='<TAG>', help=_('Name of the tag.'))
def do_md_tag_delete(gc, args):
    """Delete a specific metadata definitions tag inside a namespace."""
    gc.metadefs_tag.delete(args.namespace, args.tag)


@utils.arg('namespace', metavar='<NAMESPACE>', help=_('Name of namespace.'))
def do_md_namespace_tags_delete(gc, args):
    """Delete all metadata definitions tags inside a specific namespace."""
    gc.metadefs_tag.delete_all(args.namespace)


@utils.arg('namespace', metavar='<NAMESPACE>', help=_('Name of namespace.'))
def do_md_tag_list(gc, args):
    """List metadata definitions tags inside a specific namespace."""
    tags = gc.metadefs_tag.list(args.namespace)
    columns = ['name']
    column_settings = {
        "description": {
            "max_width": 50,
            "align": "l"
        }
    }
    utils.print_list(tags, columns, field_settings=column_settings)


@utils.arg('--target', default='both',
           choices=cache.TARGET_VALUES,
           help=_('Specify which target you want to clear'))
def do_cache_clear(gc, args):
    """Clear all images from cache, queue or both"""
    if not gc.endpoint_provided:
        utils.exit("Direct server endpoint needs to be provided. Do not use "
                   "loadbalanced or catalog endpoints.")
    try:
        gc.cache.clear(args.target)
    except exc.HTTPForbidden:
        msg = _("You are not permitted to delete image(s) "
                "from cache.")
        utils.print_err(msg)
    except exc.HTTPException as e:
        msg = _("'%s': Unable to delete image(s) from cache." % e)
        utils.print_err(msg)


@utils.arg('id', metavar='<IMAGE_ID>', nargs='+',
           help=_('ID of image(s) to delete from cache/queue.'))
def do_cache_delete(gc, args):
    """Delete image from cache/caching queue."""
    if not gc.endpoint_provided:
        utils.exit("Direct server endpoint needs to be provided. Do not use "
                   "loadbalanced or catalog endpoints.")

    for args_id in args.id:
        try:
            gc.cache.delete(args_id)
        except exc.HTTPForbidden:
            msg = _("You are not permitted to delete the image '%s' "
                    "from cache." % args_id)
            utils.print_err(msg)
        except exc.HTTPException as e:
            msg = _("'%s': Unable to delete image '%s' from cache."
                    % (e, args_id))
            utils.print_err(msg)


def do_cache_list(gc, args):
    """Get cache state."""
    if not gc.endpoint_provided:
        utils.exit("Direct server endpoint needs to be provided. Do not use "
                   "loadbalanced or catalog endpoints.")
    cached_images = gc.cache.list()
    utils.print_cached_images(cached_images)


@utils.arg('id', metavar='<IMAGE_ID>', nargs='+',
           help=_('ID of image(s) to queue for caching.'))
def do_cache_queue(gc, args):
    """Queue image(s) for caching."""
    if not gc.endpoint_provided:
        utils.exit("Direct server endpoint needs to be provided. Do not use "
                   "loadbalanced or catalog endpoints.")

    for args_id in args.id:
        try:
            gc.cache.queue(args_id)
        except exc.HTTPForbidden:
            msg = _("You are not permitted to queue the image '%s' "
                    "for caching." % args_id)
            utils.print_err(msg)
        except exc.HTTPException as e:
            msg = _("'%s': Unable to queue image '%s' for caching."
                    % (e, args_id))
            utils.print_err(msg)


@utils.arg('--sort-key', default='status',
           choices=tasks.SORT_KEY_VALUES,
           help=_('Sort task list by specified field.'))
@utils.arg('--sort-dir', default='desc',
           choices=tasks.SORT_DIR_VALUES,
           help=_('Sort task list in specified direction.'))
@utils.arg('--page-size', metavar='<SIZE>', default=None, type=int,
           help=_('Number of tasks to request in each paginated request.'))
@utils.arg('--type', metavar='<TYPE>',
           help=_('Filter tasks to those that have this type.'))
@utils.arg('--status', metavar='<STATUS>',
           help=_('Filter tasks to those that have this status.'))
def do_task_list(gc, args):
    """List tasks you can access."""
    filter_keys = ['type', 'status']
    filter_items = [(key, getattr(args, key)) for key in filter_keys]
    filters = dict([item for item in filter_items if item[1] is not None])

    kwargs = {'filters': filters}
    if args.page_size is not None:
        kwargs['page_size'] = args.page_size

    kwargs['sort_key'] = args.sort_key
    kwargs['sort_dir'] = args.sort_dir

    tasks = gc.tasks.list(**kwargs)

    columns = ['ID', 'Type', 'Status', 'Owner']
    utils.print_list(tasks, columns)


@utils.arg('id', metavar='<TASK_ID>', help=_('ID of task to describe.'))
def do_task_show(gc, args):
    """Describe a specific task."""
    task = gc.tasks.get(args.id)
    ignore = ['self', 'schema']
    task = dict([item for item in task.items() if item[0] not in ignore])
    utils.print_dict(task)


@utils.arg('--type', metavar='<TYPE>',
           help=_('Type of Task. Please refer to Glance schema or '
                  'documentation to see which tasks are supported.'))
@utils.arg('--input', metavar='<STRING>', default='{}',
           help=_('Parameters of the task to be launched'))
def do_task_create(gc, args):
    """Create a new task."""
    if not (args.type and args.input):
        utils.exit('Unable to create task. Specify task type and input.')
    else:
        try:
            input = json.loads(args.input)
        except ValueError:
            utils.exit('Failed to parse the "input" parameter. Must be a '
                       'valid JSON object.')

        task_values = {'type': args.type, 'input': input}
        task = gc.tasks.create(**task_values)
        ignore = ['self', 'schema']
        task = dict([item for item in task.items()
                     if item[0] not in ignore])
        utils.print_dict(task)
