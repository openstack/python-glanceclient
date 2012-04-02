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

import urllib

from glanceclient.common import base


class Image(base.Resource):
    def __repr__(self):
        return "<Image %s>" % self._info

    def delete(self):
        return self.manager.delete(self)


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
        for key, value in fields.iteritems():
            if key == 'properties':
                headers['x-image-meta-property-%s' % key] = value
            else:
                headers['x-image-meta-%s' % key] = value
        return headers

    def get(self, image):
        """Get the metadata for a specific image.

        :param image: image object or id to look up
        :rtype: :class:`Image`
        """
        resp, body = self.api.head('/v1/images/%s' % base.getid(image))
        meta = self._image_meta_from_headers(resp)
        return Image(self, meta)

    def list(self, limit=None, marker=None):
        """Get a list of images.

        :param limit: maximum number of images to return. Used for pagination.
        :param marker: id of image last seen by caller. Used for pagination.
        :rtype: list of :class:`Image`
        """
        params = {}
        if limit:
            params['limit'] = int(limit)
        if marker:
            params['marker'] = int(marker)
        query = '?%s' % urllib.urlencode(params) if params else ''
        return self._list('/v1/images/detail%s' % query, "images")

    def delete(self, image):
        """Delete an image."""
        self._delete("/v1/images/%s" % base.getid(image))

    def create(self, **kwargs):
        """Create an image"""
        fields = {}
        if 'name' in kwargs:
            fields['name'] = kwargs['name']
        resp, body = self.api.post('/v1/images', body={'image': fields})
        meta = self._image_meta_from_headers(resp)
        return Image(self, meta)

    def update(self, image, **kwargs):
        """Update an image"""
        fields = {}
        if 'name' in kwargs:
            fields['name'] = kwargs['name']
        send_meta = self._image_meta_to_headers(fields)
        url = '/v1/images/%s' % base.getid(image)
        resp, body = self.api.put(url, headers=send_meta)
        recv_meta = self._image_meta_from_headers(resp)
        return Image(self, recv_meta)
