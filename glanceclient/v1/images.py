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

import copy
import json
import urllib

from glanceclient.common import base
from glanceclient.common import utils
from glanceclient.openstack.common import strutils

UPDATE_PARAMS = ('name', 'disk_format', 'container_format', 'min_disk',
                 'min_ram', 'owner', 'size', 'is_public', 'protected',
                 'location', 'checksum', 'copy_from', 'properties',
                 #NOTE(bcwaldon: an attempt to update 'deleted' will be
                 # ignored, but we need to support it for backwards-
                 # compatibility with the legacy client library
                 'deleted')

CREATE_PARAMS = UPDATE_PARAMS + ('id', 'store')

DEFAULT_PAGE_SIZE = 20

SORT_DIR_VALUES = ('asc', 'desc')
SORT_KEY_VALUES = ('name', 'status', 'container_format', 'disk_format',
                   'size', 'id', 'created_at', 'updated_at')


class Image(base.Resource):
    def __repr__(self):
        return "<Image %s>" % self._info

    def update(self, **fields):
        self.manager.update(self, **fields)

    def delete(self):
        return self.manager.delete(self)

    def data(self, **kwargs):
        return self.manager.data(self, **kwargs)


class ImageManager(base.Manager):
    resource_class = Image

    def _image_meta_from_headers(self, headers):
        meta = {'properties': {}}
        safe_decode = strutils.safe_decode
        for key, value in headers.iteritems():
            value = safe_decode(value, incoming='utf-8')
            if key.startswith('x-image-meta-property-'):
                _key = safe_decode(key[22:], incoming='utf-8')
                meta['properties'][_key] = value
            elif key.startswith('x-image-meta-'):
                _key = safe_decode(key[13:], incoming='utf-8')
                meta[_key] = value

        for key in ['is_public', 'protected', 'deleted']:
            if key in meta:
                meta[key] = utils.string_to_bool(meta[key])

        return self._format_image_meta_for_user(meta)

    def _image_meta_to_headers(self, fields):
        headers = {}
        fields_copy = copy.deepcopy(fields)

        # NOTE(flaper87): Convert to str, headers
        # that are not instance of basestring. All
        # headers will be encoded later, before the
        # request is sent.
        def to_str(value):
            if not isinstance(value, basestring):
                return str(value)
            return value

        for key, value in fields_copy.pop('properties', {}).iteritems():
            headers['x-image-meta-property-%s' % key] = to_str(value)
        for key, value in fields_copy.iteritems():
            headers['x-image-meta-%s' % key] = to_str(value)
        return headers

    @staticmethod
    def _format_image_meta_for_user(meta):
        for key in ['size', 'min_ram', 'min_disk']:
            if key in meta:
                try:
                    meta[key] = int(meta[key])
                except ValueError:
                    pass
        return meta

    def get(self, image):
        """Get the metadata for a specific image.

        :param image: image object or id to look up
        :rtype: :class:`Image`
        """

        image_id = base.getid(image)
        resp, body = self.api.raw_request('HEAD', '/v1/images/%s'
                                          % urllib.quote(str(image_id)))
        meta = self._image_meta_from_headers(dict(resp.getheaders()))
        return Image(self, meta)

    def data(self, image, do_checksum=True):
        """Get the raw data for a specific image.

        :param image: image object or id to look up
        :param do_checksum: Enable/disable checksum validation
        :rtype: iterable containing image data
        """
        image_id = base.getid(image)
        resp, body = self.api.raw_request('GET', '/v1/images/%s'
                                          % urllib.quote(str(image_id)))
        checksum = resp.getheader('x-image-meta-checksum', None)
        if do_checksum and checksum is not None:
            body.set_checksum(checksum)
        return body

    def list(self, **kwargs):
        """Get a list of images.

        :param page_size: number of items to request in each paginated request
        :param limit: maximum number of images to return
        :param marker: begin returning images that appear later in the image
                       list than that represented by this image id
        :param filters: dict of direct comparison filters that mimics the
                        structure of an image object
        :param owner: If provided, only images with this owner (tenant id)
                      will be listed. An empty string ('') matches ownerless
                      images.
        :rtype: list of :class:`Image`
        """
        absolute_limit = kwargs.get('limit')

        def paginate(qp, seen=0):
            def filter_owner(owner, image):
                # If client side owner 'filter' is specified
                # only return images that match 'owner'.
                if owner is None:
                    # Do not filter based on owner
                    return False
                if (not hasattr(image, 'owner')) or image.owner is None:
                    # ownerless image
                    return not (owner == '')
                else:
                    return not (image.owner == owner)

            owner = qp.pop('owner', None)
            for param, value in qp.iteritems():
                if isinstance(value, basestring):
                    # Note(flaper87) Url encoding should
                    # be moved inside http utils, at least
                    # shouldn't be here.
                    #
                    # Making sure all params are str before
                    # trying to encode them
                    qp[param] = strutils.safe_encode(value)

            url = '/v1/images/detail?%s' % urllib.urlencode(qp)
            images = self._list(url, "images")
            for image in images:
                if filter_owner(owner, image):
                    continue
                seen += 1
                if absolute_limit is not None and seen > absolute_limit:
                    return
                yield image

            page_size = qp.get('limit')
            if (page_size and len(images) == page_size and
                    (absolute_limit is None or 0 < seen < absolute_limit)):
                qp['marker'] = image.id
                for image in paginate(qp, seen):
                    yield image

        params = {'limit': kwargs.get('page_size', DEFAULT_PAGE_SIZE)}

        if 'marker' in kwargs:
            params['marker'] = kwargs['marker']

        sort_key = kwargs.get('sort_key')
        if sort_key is not None:
            if sort_key in SORT_KEY_VALUES:
                params['sort_key'] = sort_key
            else:
                raise ValueError('sort_key must be one of the following: %s.'
                                 % ', '.join(SORT_KEY_VALUES))

        sort_dir = kwargs.get('sort_dir')
        if sort_dir is not None:
            if sort_dir in SORT_DIR_VALUES:
                params['sort_dir'] = sort_dir
            else:
                raise ValueError('sort_dir must be one of the following: %s.'
                                 % ', '.join(SORT_DIR_VALUES))

        filters = kwargs.get('filters', {})
        properties = filters.pop('properties', {})
        for key, value in properties.items():
            params['property-%s' % key] = value
        params.update(filters)
        if kwargs.get('owner') is not None:
            params['owner'] = kwargs['owner']
            params['is_public'] = None
        if 'is_public' in kwargs:
            params['is_public'] = kwargs['is_public']

        return paginate(params)

    def delete(self, image):
        """Delete an image."""
        self._delete("/v1/images/%s" % base.getid(image))

    def create(self, **kwargs):
        """Create an image

        TODO(bcwaldon): document accepted params
        """
        image_data = kwargs.pop('data', None)
        if image_data is not None:
            image_size = utils.get_file_size(image_data)
            if image_size is not None:
                kwargs.setdefault('size', image_size)

        fields = {}
        for field in kwargs:
            if field in CREATE_PARAMS:
                fields[field] = kwargs[field]
            else:
                msg = 'create() got an unexpected keyword argument \'%s\''
                raise TypeError(msg % field)

        copy_from = fields.pop('copy_from', None)
        hdrs = self._image_meta_to_headers(fields)
        if copy_from is not None:
            hdrs['x-glance-api-copy-from'] = copy_from

        resp, body_iter = self.api.raw_request(
            'POST', '/v1/images', headers=hdrs, body=image_data)
        body = json.loads(''.join([c for c in body_iter]))
        return Image(self, self._format_image_meta_for_user(body['image']))

    def update(self, image, **kwargs):
        """Update an image

        TODO(bcwaldon): document accepted params
        """
        image_data = kwargs.pop('data', None)
        if image_data is not None:
            image_size = utils.get_file_size(image_data)
            if image_size is not None:
                kwargs.setdefault('size', image_size)

        hdrs = {}
        try:
            purge_props = 'true' if kwargs.pop('purge_props') else 'false'
        except KeyError:
            pass
        else:
            hdrs['x-glance-registry-purge-props'] = purge_props

        fields = {}
        for field in kwargs:
            if field in UPDATE_PARAMS:
                fields[field] = kwargs[field]
            else:
                msg = 'update() got an unexpected keyword argument \'%s\''
                raise TypeError(msg % field)

        copy_from = fields.pop('copy_from', None)
        hdrs.update(self._image_meta_to_headers(fields))
        if copy_from is not None:
            hdrs['x-glance-api-copy-from'] = copy_from

        url = '/v1/images/%s' % base.getid(image)
        resp, body_iter = self.api.raw_request(
            'PUT', url, headers=hdrs, body=image_data)
        body = json.loads(''.join([c for c in body_iter]))
        return Image(self, self._format_image_meta_for_user(body['image']))
