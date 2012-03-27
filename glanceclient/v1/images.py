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

    def get(self, image):
        """Get the metadata for a specific image.

        :param image: image object or id to look up
        :rtype: :class:`Image`
        """
        resp, body = self.api.head("/images/%s" % base.getid(image))
        meta = {'properties': {}}
        for key, value in resp.iteritems():
            if key.startswith('x-image-meta-property-'):
                _key = key[22:]
                meta['properties'][_key] = value
            elif key.startswith('x-image-meta-'):
                _key = key[13:]
                meta[_key] = value
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

        query = ""
        if params:
            query = "?" + urllib.urlencode(params)

        return self._list("/images/detail%s" % query, "images")

    def delete(self, image):
        """Delete an image."""
        self._delete("/images/%s" % base.getid(image))
