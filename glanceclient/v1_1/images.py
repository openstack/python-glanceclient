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

import urllib

from glanceclient import base


class Image(base.Resource):
    def __repr__(self):
        return "<Image %s>" % self._info

    def delete(self):
        return self.manager.delete(self)

    def list_roles(self, tenant=None):
        return self.manager.list_roles(self.id, base.getid(tenant))


class ImageManager(base.ManagerWithFind):
    resource_class = Image

    def get(self, image):
        return self._get("/images/%s" % base.getid(image), "image")

    def update(self, image, **kwargs):
        """
        Update image data.

        Supported arguments include ``name`` and ``is_public``.
        """
        params = {"image": kwargs}
        params['image']['id'] = base.getid(image)
        url = "/images/%s" % base.getid(image)
        return self._update(url, params, "image")

    def create(self, name, is_public=True):
        """
        Create an image.
        """
        params = {
            "image": {
                "name": name,
                "is_public": is_public
            }
        }
        return self._create('/images', params, "image")

    def delete(self, image):
        """
        Delete a image.
        """
        return self._delete("/images/%s" % base.getid(image))

    def list(self, limit=None, marker=None):
        """
        Get a list of images (optionally limited to a tenant)

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

        return self._list("/images%s" % query, "images")

    def list_members(self, image):
        return self.api.members.members_for_image(base.getid(image))
