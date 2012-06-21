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

import copy
import errno
import json
import os
import urllib

from glanceclient.common import base

UPDATE_PARAMS = ('name', 'disk_format', 'container_format', 'min_disk',
                 'min_ram', 'owner', 'size', 'is_public', 'protected',
                 'location', 'checksum', 'copy_from', 'properties')

CREATE_PARAMS = UPDATE_PARAMS + ('id',)


class Image(base.Resource):
    def __repr__(self):
        return "<Image %s>" % self._info

    def update(self, **fields):
        self.manager.update(self, **fields)

    def delete(self):
        return self.manager.delete(self)

    def data(self):
        return self.manager.data(self)


class ImageManager(base.Manager):
    resource_class = Image

    def _image_meta_from_headers(self, headers):
        meta = {'properties': {}}
        for key, value in headers.iteritems():
            if key.startswith('x-image-meta-property-'):
                _key = key[22:]
                meta['properties'][_key] = value
            elif key.startswith('x-image-meta-'):
                _key = key[13:]
                meta[_key] = value
        return meta

    def _image_meta_to_headers(self, fields):
        headers = {}
        fields_copy = copy.deepcopy(fields)
        for key, value in fields_copy.pop('properties', {}).iteritems():
            headers['x-image-meta-property-%s' % key] = str(value)
        for key, value in fields_copy.iteritems():
            headers['x-image-meta-%s' % key] = str(value)
        return headers

    def get(self, image_id):
        """Get the metadata for a specific image.

        :param image: image object or id to look up
        :rtype: :class:`Image`
        """
        resp, body = self.api.raw_request('HEAD', '/v1/images/%s' % image_id)
        meta = self._image_meta_from_headers(resp)
        return Image(self, meta)

    def data(self, image):
        """Get the raw data for a specific image.

        :param image: image object or id to look up
        :rtype: iterable containing image data
        """
        image_id = base.getid(image)
        resp, body = self.api.raw_request('GET', '/v1/images/%s' % image_id)
        return body

    def list(self, limit=None, marker=None, filters=None):
        """Get a list of images.

        :param limit: maximum number of images to return. Used for pagination.
        :param marker: id of image last seen by caller. Used for pagination.
        :rtype: list of :class:`Image`
        """
        params = {}
        if limit:
            params['limit'] = int(limit)
        if marker:
            params['marker'] = marker
        if filters:
            params.update(filters)
        query = '?%s' % urllib.urlencode(params) if params else ''
        return self._list('/v1/images/detail%s' % query, "images")

    def delete(self, image):
        """Delete an image."""
        self._delete("/v1/images/%s" % base.getid(image))

    def _get_file_size(self, obj):
        """Analyze file-like object and attempt to determine its size.

        :param obj: file-like object, typically redirected from stdin.
        :retval The file's size or None if it cannot be determined.
        """
        # For large images, we need to supply the size of the
        # image file. See LP Bugs #827660 and #845788.
        if hasattr(obj, 'seek') and hasattr(obj, 'tell'):
            try:
                obj.seek(0, os.SEEK_END)
                obj_size = obj.tell()
                obj.seek(0)
                return obj_size
            except IOError, e:
                if e.errno == errno.ESPIPE:
                    # Illegal seek. This means the user is trying
                    # to pipe image data to the client, e.g.
                    # echo testdata | bin/glance add blah..., or
                    # that stdin is empty
                    return 0
                else:
                    raise

    def create(self, **kwargs):
        """Create an image

        TODO(bcwaldon): document accepted params
        """
        image_data = kwargs.pop('data', None)
        if image_data is not None:
            image_size = self._get_file_size(image_data)
            if image_size != 0:
                kwargs.setdefault('size', image_size)
            else:
                image_data = None

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

        resp, body = self.api.raw_request(
                'POST', '/v1/images', headers=hdrs, body=image_data)
        return Image(self, json.loads(body)['image'])

    def update(self, image, **kwargs):
        """Update an image

        TODO(bcwaldon): document accepted params
        """
        image_data = kwargs.pop('data', None)
        if image_data is not None:
            image_size = self._get_file_size(image_data)
            if image_size != 0:
                kwargs.setdefault('size', image_size)
            else:
                image_data = None

        fields = {}
        for field in kwargs:
            if field in UPDATE_PARAMS:
                fields[field] = kwargs[field]
            else:
                msg = 'update() got an unexpected keyword argument \'%s\''
                raise TypeError(msg % field)

        copy_from = fields.pop('copy_from', None)
        hdrs = self._image_meta_to_headers(fields)
        if copy_from is not None:
            hdrs['x-glance-api-copy-from'] = copy_from

        url = '/v1/images/%s' % base.getid(image)
        resp, body = self.api.raw_request(
                'PUT', url, headers=hdrs, body=image_data)
        return Image(self, json.loads(body)['image'])
