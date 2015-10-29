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

from glanceclient.common import http
from glanceclient.common import utils
from glanceclient.v1 import image_members
from glanceclient.v1 import images
from glanceclient.v1 import versions


class Client(object):
    """Client for the OpenStack Images v1 API.

    :param string endpoint: A user-supplied endpoint URL for the glance
                            service.
    :param string token: Token for authentication.
    :param integer timeout: Allows customization of the timeout for client
                            http requests. (optional)
    :param string language_header: Set Accept-Language header to be sent in
                                   requests to glance.
    """

    def __init__(self, endpoint=None, **kwargs):
        """Initialize a new client for the Images v1 API."""
        endpoint, self.version = utils.endpoint_version_from_url(endpoint, 1.0)
        self.http_client = http.get_http_client(endpoint=endpoint, **kwargs)
        self.images = images.ImageManager(self.http_client)
        self.image_members = image_members.ImageMemberManager(self.http_client)
        self.versions = versions.VersionManager(self.http_client)
