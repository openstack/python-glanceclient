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

import hashlib
import json
from oslo_utils import encodeutils
from requests import codes
import urllib.parse
import warlock

from glanceclient.common import utils
from glanceclient import exc
from glanceclient.v2 import schemas

DEFAULT_PAGE_SIZE = 200

SORT_DIR_VALUES = ('asc', 'desc')
SORT_KEY_VALUES = ('name', 'status', 'container_format', 'disk_format',
                   'size', 'id', 'created_at', 'updated_at')


class Controller(object):
    def __init__(self, http_client, schema_client):
        self.http_client = http_client
        self.schema_client = schema_client

    @utils.memoized_property
    def model(self):
        schema = self.schema_client.get('image')
        warlock_model = warlock.model_factory(
            schema.raw(), base_class=schemas.SchemaBasedModel)
        return warlock_model

    @utils.memoized_property
    def unvalidated_model(self):
        """A model which does not validate the image against the v2 schema."""
        schema = self.schema_client.get('image')
        warlock_model = warlock.model_factory(
            schema.raw(), base_class=schemas.SchemaBasedModel)
        warlock_model.validate = lambda *args, **kwargs: None
        return warlock_model

    @staticmethod
    def _wrap(value):
        if isinstance(value, str):
            return [value]
        return value

    @staticmethod
    def _validate_sort_param(sort):
        """Validates sorting argument for invalid keys and directions values.

        :param sort: comma-separated list of sort keys with optional <:dir>
        after each key
        """
        for sort_param in sort.strip().split(','):
            key, _sep, dir = sort_param.partition(':')
            if dir and dir not in SORT_DIR_VALUES:
                msg = ('Invalid sort direction: %(sort_dir)s.'
                       ' It must be one of the following: %(available)s.'
                       ) % {'sort_dir': dir,
                            'available': ', '.join(SORT_DIR_VALUES)}
                raise exc.HTTPBadRequest(msg)
            if key not in SORT_KEY_VALUES:
                msg = ('Invalid sort key: %(sort_key)s.'
                       ' It must be one of the following: %(available)s.'
                       ) % {'sort_key': key,
                            'available': ', '.join(SORT_KEY_VALUES)}
                raise exc.HTTPBadRequest(msg)
        return sort

    @utils.add_req_id_to_generator()
    def list(self, **kwargs):
        """Retrieve a listing of Image objects.

        :param page_size: Number of images to request in each
                          paginated request.
        :returns: generator over list of Images.
        """

        limit = kwargs.get('limit')
        # NOTE(flaper87): Don't use `get('page_size', DEFAULT_SIZE)` otherwise,
        # it could be possible to send invalid data to the server by passing
        # page_size=None.
        page_size = kwargs.get('page_size') or DEFAULT_PAGE_SIZE

        def paginate(url, page_size, limit=None):
            next_url = url
            req_id_hdr = {}

            while True:
                if limit and page_size > limit:
                    # NOTE(flaper87): Avoid requesting 2000 images when limit
                    # is 1
                    next_url = next_url.replace("limit=%s" % page_size,
                                                "limit=%s" % limit)

                resp, body = self.http_client.get(next_url, headers=req_id_hdr)
                # NOTE(rsjethani): Store curent request id so that it can be
                # used in subsequent requests. Refer bug #1525259
                req_id_hdr['x-openstack-request-id'] = \
                    utils._extract_request_id(resp)

                for image in body['images']:
                    # NOTE(bcwaldon): remove 'self' for now until we have
                    # an elegant way to pass it into the model constructor
                    # without conflict.
                    image.pop('self', None)
                    # We do not validate the model when listing.
                    # This prevents side-effects of injecting invalid
                    # schema values via v1.
                    yield self.unvalidated_model(**image), resp
                    if limit:
                        limit -= 1
                        if limit <= 0:
                            return

                try:
                    next_url = body['next']
                except KeyError:
                    return

        filters = kwargs.get('filters', {})
        # NOTE(flaper87): We paginate in the client, hence we use
        # the page_size as Glance's limit.
        filters['limit'] = page_size

        tags = filters.pop('tag', [])
        tags_url_params = []

        for tag in tags:
            if not isinstance(tag, str):
                raise exc.HTTPBadRequest("Invalid tag value %s" % tag)

            tags_url_params.append({'tag': encodeutils.safe_encode(tag)})

        for param, value in filters.items():
            if isinstance(value, str):
                filters[param] = encodeutils.safe_encode(value)

        url = '/v2/images?%s' % urllib.parse.urlencode(filters)

        for param in tags_url_params:
            url = '%s&%s' % (url, urllib.parse.urlencode(param))

        if 'sort' in kwargs:
            if 'sort_key' in kwargs or 'sort_dir' in kwargs:
                raise exc.HTTPBadRequest("The 'sort' argument is not supported"
                                         " with 'sort_key' or 'sort_dir'.")
            url = '%s&sort=%s' % (url,
                                  self._validate_sort_param(
                                      kwargs['sort']))
        else:
            sort_dir = self._wrap(kwargs.get('sort_dir', []))
            sort_key = self._wrap(kwargs.get('sort_key', []))

            if len(sort_key) != len(sort_dir) and len(sort_dir) > 1:
                raise exc.HTTPBadRequest(
                    "Unexpected number of sort directions: "
                    "either provide a single sort direction or an equal "
                    "number of sort keys and sort directions.")
            for key in sort_key:
                url = '%s&sort_key=%s' % (url, key)

            for dir in sort_dir:
                url = '%s&sort_dir=%s' % (url, dir)

        if isinstance(kwargs.get('marker'), str):
            url = '%s&marker=%s' % (url, kwargs['marker'])

        for image, resp in paginate(url, page_size, limit):
            yield image, resp

    @utils.add_req_id_to_object()
    def _get(self, image_id, header=None):
        url = '/v2/images/%s' % image_id
        header = header or {}
        resp, body = self.http_client.get(url, headers=header)
        # NOTE(bcwaldon): remove 'self' for now until we have an elegant
        # way to pass it into the model constructor without conflict
        body.pop('self', None)
        return self.unvalidated_model(**body), resp

    def get(self, image_id):
        return self._get(image_id)

    @utils.add_req_id_to_object()
    def get_associated_image_tasks(self, image_id):
        """Get the tasks associated with an image.

        :param image_id: ID of the image
        :raises: exc.HTTPNotImplemented if Glance is not new enough to support
                 this API (v2.12).
        """
        # NOTE (abhishekk): Verify that /v2i/images/%s/tasks is supported by
        # glance
        if utils.has_version(self.http_client, 'v2.12'):
            url = '/v2/images/%s/tasks' % image_id
            resp, body = self.http_client.get(url)
            body.pop('self', None)
            return body, resp
        else:
            raise exc.HTTPNotImplemented(
                'This operation is not supported by Glance.')

    @utils.add_req_id_to_object()
    def data(self, image_id, do_checksum=True, allow_md5_fallback=False):
        """Retrieve data of an image.

        When do_checksum is enabled, validation proceeds as follows:

        1. if the image has a 'os_hash_value' property, the algorithm
           specified in the image's 'os_hash_algo' property will be used
           to validate against the 'os_hash_value' value.  If the
           specified hash algorithm is not available AND allow_md5_fallback
           is True, then continue to step #2
        2. else if the image has a checksum property, MD5 is used to
           validate against the 'checksum' value.  (If MD5 is not available
           to the client, the download fails.)
        3. else if the download response has a 'content-md5' header, MD5
           is used to validate against the header value.  (If MD5 is not
           available to the client, the download fails.)
        4. if none of 1-3 obtain, the data is **not validated** (this is
           compatible with legacy behavior)

        :param image_id:    ID of the image to download
        :param do_checksum: Enable/disable checksum validation
        :param allow_md5_fallback:
            Use the MD5 checksum for validation if the algorithm specified by
            the image's 'os_hash_algo' property is not available
        :returns: An iterable body or ``None``
        """
        if do_checksum:
            # doing this first to prevent race condition if image record
            # is deleted during the image download
            url = '/v2/images/%s' % image_id
            resp, image_meta = self.http_client.get(url)
            meta_checksum = image_meta.get('checksum', None)
            meta_hash_value = image_meta.get('os_hash_value', None)
            meta_hash_algo = image_meta.get('os_hash_algo', None)

        url = '/v2/images/%s/file' % image_id
        resp, body = self.http_client.get(url)
        if resp.status_code == codes.no_content:
            return None, resp

        checksum = resp.headers.get('content-md5', None)
        content_length = int(resp.headers.get('content-length', 0))

        check_md5sum = do_checksum
        if do_checksum and meta_hash_value is not None:
            try:
                hasher = hashlib.new(str(meta_hash_algo))
                body = utils.serious_integrity_iter(body,
                                                    hasher,
                                                    meta_hash_value)
                check_md5sum = False
            except ValueError as ve:
                if (str(ve).startswith('unsupported hash type') and
                        allow_md5_fallback):
                    check_md5sum = True
                else:
                    raise

        if do_checksum and check_md5sum:
            if meta_checksum is not None:
                body = utils.integrity_iter(body, meta_checksum)
            elif checksum is not None:
                body = utils.integrity_iter(body, checksum)
            else:
                # NOTE(rosmaita): this preserves legacy behavior to return the
                # image data when checksumming is requested but there's no
                # 'content-md5' header in the response.  Just want to make it
                # clear that we're doing this on purpose.
                pass

        return utils.IterableWithLength(body, content_length), resp

    @utils.add_req_id_to_object()
    def upload(self, image_id, image_data, image_size=None, u_url=None,
               backend=None):
        """Upload the data for an image.

        :param image_id: ID of the image to upload data for.
        :param image_data: File-like object supplying the data to upload.
        :param image_size: If present pass it as header
        :param u_url: Upload url to upload the data to.
        :param backend: Backend store to upload image to.
        """
        url = u_url or '/v2/images/%s/file' % image_id
        hdrs = {'Content-Type': 'application/octet-stream'}
        if image_size is not None:
            if not isinstance(image_size, int):
                raise TypeError("image_size must be an integer, "
                                "got %s" % type(image_size).__name__)
            hdrs.update({'x-openstack-image-size': '%i' % image_size})
        if backend is not None:
            hdrs['x-image-meta-store'] = backend

        body = image_data
        resp, body = self.http_client.put(url, headers=hdrs, data=body)
        return (resp, body), resp

    @utils.add_req_id_to_object()
    def get_import_info(self):
        """Get Import info from discovery endpoint."""
        url = '/v2/info/import'
        resp, body = self.http_client.get(url)
        return body, resp

    @utils.add_req_id_to_object()
    def get_stores_info(self):
        """Get available stores info from discovery endpoint."""
        url = '/v2/info/stores'
        resp, body = self.http_client.get(url)
        return body, resp

    @utils.add_req_id_to_object()
    def get_stores_info_detail(self):
        """Get available stores info from discovery endpoint."""
        url = '/v2/info/stores/detail'
        resp, body = self.http_client.get(url)
        return body, resp

    @utils.add_req_id_to_object()
    def delete_from_store(self, store_id, image_id):
        """Delete image data from specific store."""
        url = ('/v2/stores/%(store)s/%(image)s' % {'store': store_id,
                                                   'image': image_id})
        resp, body = self.http_client.delete(url)
        return body, resp

    @utils.add_req_id_to_object()
    def stage(self, image_id, image_data, image_size=None):
        """Upload the data to image staging.

        :param image_id: ID of the image to upload data for.
        :param image_data: File-like object supplying the data to upload.
        :param image_size: If present pass it to upload call
        """
        url = '/v2/images/%s/stage' % image_id
        resp, body = self.upload(image_id,
                                 image_data,
                                 image_size=image_size,
                                 u_url=url)
        return body, resp

    @utils.add_req_id_to_object()
    def image_import(self, image_id, method='glance-direct', uri=None,
                     remote_region=None, remote_image_id=None,
                     remote_service_interface=None, backend=None,
                     stores=None, allow_failure=True, all_stores=None):
        """Import Image via method."""
        headers = {}
        url = '/v2/images/%s/import' % image_id
        data = {'method': {'name': method}}
        if stores:
            data['stores'] = stores
            if allow_failure:
                data['all_stores_must_succeed'] = False
        if backend is not None:
            headers['x-image-meta-store'] = backend
        if all_stores:
            data['all_stores'] = True
            if allow_failure:
                data['all_stores_must_succeed'] = False

        if remote_region and remote_image_id:
            if remote_service_interface:
                data['method']['glance_service_interface'] = \
                    remote_service_interface
            data['method']['glance_region'] = remote_region
            data['method']['glance_image_id'] = remote_image_id

        if uri:
            if method == 'web-download':
                data['method']['uri'] = uri
            else:
                raise exc.HTTPBadRequest('URI is only supported with method: '
                                         '"web-download"')
        resp, body = self.http_client.post(url, data=data, headers=headers)
        return body, resp

    @utils.add_req_id_to_object()
    def delete(self, image_id):
        """Delete an image."""
        url = '/v2/images/%s' % image_id
        resp, body = self.http_client.delete(url)
        return (resp, body), resp

    @utils.add_req_id_to_object()
    def create(self, **kwargs):
        """Create an image."""
        headers = {}
        url = '/v2/images'
        backend = kwargs.pop('backend', None)
        if backend is not None:
            headers['x-image-meta-store'] = backend

        image = self.model()
        for (key, value) in kwargs.items():
            try:
                setattr(image, key, value)
            except warlock.InvalidOperation as e:
                raise TypeError(str(e))

        resp, body = self.http_client.post(url, headers=headers, data=image)
        # NOTE(esheffield): remove 'self' for now until we have an elegant
        # way to pass it into the model constructor without conflict
        body.pop('self', None)
        return self.model(**body), resp

    @utils.add_req_id_to_object()
    def deactivate(self, image_id):
        """Deactivate an image."""
        url = '/v2/images/%s/actions/deactivate' % image_id
        resp, body = self.http_client.post(url)
        return (resp, body), resp

    @utils.add_req_id_to_object()
    def reactivate(self, image_id):
        """Reactivate an image."""
        url = '/v2/images/%s/actions/reactivate' % image_id
        resp, body = self.http_client.post(url)
        return (resp, body), resp

    def update(self, image_id, remove_props=None, **kwargs):
        """Update attributes of an image.

        :param image_id: ID of the image to modify.
        :param remove_props: List of property names to remove
        :param kwargs: Image attribute names and their new values.
        """
        unvalidated_image = self.get(image_id)
        image = self.model(**unvalidated_image)
        for (key, value) in kwargs.items():
            try:
                setattr(image, key, value)
            except warlock.InvalidOperation as e:
                raise TypeError(str(e))

        if remove_props:
            cur_props = image.keys()
            new_props = kwargs.keys()
            # NOTE(esheffield): Only remove props that currently exist on the
            # image and are NOT in the properties being updated / added
            props_to_remove = set(cur_props).intersection(
                set(remove_props).difference(new_props))

            for key in props_to_remove:
                delattr(image, key)

        url = '/v2/images/%s' % image_id
        hdrs = {'Content-Type': 'application/openstack-images-v2.1-json-patch'}
        resp, _ = self.http_client.patch(url, headers=hdrs, data=image.patch)
        # Get request id from `patch` request so it can be passed to the
        #  following `get` call
        req_id_hdr = {
            'x-openstack-request-id': utils._extract_request_id(resp)}

        # NOTE(bcwaldon): calling image.patch doesn't clear the changes, so
        # we need to fetch the image again to get a clean history. This is
        # an obvious optimization for warlock
        return self._get(image_id, req_id_hdr)

    def _get_image_with_locations_or_fail(self, image_id):
        image = self.get(image_id)
        if getattr(image, 'locations', None) is None:
            raise exc.HTTPBadRequest('The administrator has disabled '
                                     'API access to image locations')
        return image

    @utils.add_req_id_to_object()
    def _send_image_update_request(self, image_id, patch_body):
        url = '/v2/images/%s' % image_id
        hdrs = {'Content-Type': 'application/openstack-images-v2.1-json-patch'}
        resp, body = self.http_client.patch(url, headers=hdrs,
                                            data=json.dumps(patch_body))
        return (resp, body), resp

    def add_location(self, image_id, url, metadata, validation_data=None):
        """Add a new location entry to an image's list of locations.

        It is an error to add a URL that is already present in the list of
        locations.

        :param image_id: ID of image to which the location is to be added.
        :param url: URL of the location to add.
        :param metadata: Metadata associated with the location.
        :param validation_data: Validation data for the image.
        :returns: The updated image
        """
        add_patch = [{'op': 'add', 'path': '/locations/-',
                      'value': {'url': url, 'metadata': metadata}}]
        if validation_data:
            add_patch[0]['value']['validation_data'] = validation_data
        response = self._send_image_update_request(image_id, add_patch)
        # Get request id from the above update request and pass the same to
        # following get request
        req_id_hdr = {'x-openstack-request-id': response.request_ids[0]}
        return self._get(image_id, req_id_hdr)

    def delete_locations(self, image_id, url_set):
        """Remove one or more location entries of an image.

        :param image_id: ID of image from which locations are to be removed.
        :param url_set: set of URLs of location entries to remove.
        :returns: None
        """
        image = self._get_image_with_locations_or_fail(image_id)
        current_urls = [loc['url'] for loc in image.locations]

        missing_locs = url_set.difference(set(current_urls))
        if missing_locs:
            raise exc.HTTPNotFound('Unknown URL(s): %s' % list(missing_locs))

        # NOTE: warlock doesn't generate the most efficient patch for remove
        # operations (it shifts everything up and deletes the tail elements) so
        # we do it ourselves.
        url_indices = [current_urls.index(url) for url in url_set]
        url_indices.sort(reverse=True)
        patches = [{'op': 'remove', 'path': '/locations/%s' % url_idx}
                   for url_idx in url_indices]
        return self._send_image_update_request(image_id, patches)

    def update_location(self, image_id, url, metadata):
        """Update an existing location entry in an image's list of locations.

        The URL specified must be already present in the image's list of
        locations.

        :param image_id: ID of image whose location is to be updated.
        :param url: URL of the location to update.
        :param metadata: Metadata associated with the location.
        :returns: The updated image
        """
        image = self._get_image_with_locations_or_fail(image_id)
        url_map = dict([(loc['url'], loc) for loc in image.locations])
        if url not in url_map:
            raise exc.HTTPNotFound('Unknown URL: %s, the URL must be one of'
                                   ' existing locations of current image' %
                                   url)

        if url_map[url]['metadata'] == metadata:
            return image

        url_map[url]['metadata'] = metadata
        patches = [{'op': 'replace',
                    'path': '/locations',
                    'value': list(url_map.values())}]
        response = self._send_image_update_request(image_id, patches)
        # Get request id from the above update request and pass the same to
        # following get request
        req_id_hdr = {'x-openstack-request-id': response.request_ids[0]}

        return self._get(image_id, req_id_hdr)

    def add_image_location(self, image_id, location_url, validation_data={}):
        """Add a new location to an image.

        :param image_id: ID of image to which the location is to be added.
        :param location_url: URL of the location to add.
        :param validation_data: Validation data for the image.
        """
        if not utils.has_version(self.http_client, 'v2.17'):
            raise exc.HTTPNotImplemented(
                'This operation is not supported by Glance.')

        url = '/v2/images/%s/locations' % image_id
        data = {'url': location_url,
                'validation_data': validation_data}
        resp, body = self.http_client.post(url, data=data)
        return self._get(image_id)

    @utils.add_req_id_to_object()
    def get_image_locations(self, image_id):
        """Fetch list of locations associated to the Image.

        :param image_id: ID of image to which the location is to be fetched.
        """
        if not utils.has_version(self.http_client, 'v2.17'):
            raise exc.HTTPNotImplemented(
                'This operation is not supported by Glance.')
        url = '/v2/images/%s/locations' % (image_id)
        resp, locations = self.http_client.get(url)
        return locations, resp
