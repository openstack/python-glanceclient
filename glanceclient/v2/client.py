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

import warlock

from glanceclient.common import http
from glanceclient.common import utils
from glanceclient.v2 import image_members
from glanceclient.v2 import image_tags
from glanceclient.v2 import images
from glanceclient.v2 import metadefs
from glanceclient.v2 import schemas


class Client(object):
    """Client for the OpenStack Images v2 API.

    :param string endpoint: A user-supplied endpoint URL for the glance
                            service.
    :param string token: Token for authentication.
    :param integer timeout: Allows customization of the timeout for client
                            http requests. (optional)
    """

    def __init__(self, endpoint, *args, **kwargs):
        self.http_client = http.HTTPClient(utils.strip_version(endpoint),
                                           *args, **kwargs)
        self.schemas = schemas.Controller(self.http_client)
        image_model = self._get_image_model()
        self.images = images.Controller(self.http_client,
                                        image_model)
        self.image_tags = image_tags.Controller(self.http_client, image_model)
        self.image_members = image_members.Controller(self.http_client,
                                                      self._get_member_model())

        resource_type_model = self._get_metadefs_resource_type_model()
        self.metadefs_resource_type = (
            metadefs.ResourceTypeController(self.http_client,
                                            resource_type_model))

        property_model = self._get_metadefs_property_model()
        self.metadefs_property = (
            metadefs.PropertyController(self.http_client, property_model))

        object_model = self._get_metadefs_object_model()
        self.metadefs_object = (
            metadefs.ObjectController(self.http_client, object_model))

        namespace_model = self._get_metadefs_namespace_model()
        self.metadefs_namespace = (
            metadefs.NamespaceController(self.http_client, namespace_model))

    def _get_image_model(self):
        schema = self.schemas.get('image')
        return warlock.model_factory(schema.raw(), schemas.SchemaBasedModel)

    def _get_member_model(self):
        schema = self.schemas.get('member')
        return warlock.model_factory(schema.raw(), schemas.SchemaBasedModel)

    def _get_metadefs_namespace_model(self):
        schema = self.schemas.get('metadefs/namespace')
        return warlock.model_factory(schema.raw(), schemas.SchemaBasedModel)

    def _get_metadefs_resource_type_model(self):
        schema = self.schemas.get('metadefs/resource_type')
        return warlock.model_factory(schema.raw(), schemas.SchemaBasedModel)

    def _get_metadefs_property_model(self):
        schema = self.schemas.get('metadefs/property')
        return warlock.model_factory(schema.raw(), schemas.SchemaBasedModel)

    def _get_metadefs_object_model(self):
        schema = self.schemas.get('metadefs/object')
        return warlock.model_factory(schema.raw(), schemas.SchemaBasedModel)
