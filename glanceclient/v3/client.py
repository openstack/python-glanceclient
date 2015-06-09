# Copyright (c) 2015 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


from glanceclient.common import http
from glanceclient.common import utils
from glanceclient.v3 import artifacts


class Client(object):
    """Client for the OpenStack Glance v3 API.

    :param string endpoint: A user-supplied endpoint URL for the glance
                            service.
    :param string token: Token for authentication.
    :param integer timeout: Allows customization of the timeout for client
                            http requests. (optional)
    """

    def __init__(self, endpoint, type_name, type_version, **kwargs):
        endpoint, version = utils.strip_version(endpoint)
        self.version = version or 3.0
        self.http_client = http.HTTPClient(endpoint, **kwargs)

        self.type_name = type_name
        self.type_version = type_version

        self.artifacts = artifacts.Controller(self.http_client,
                                              self.type_name,
                                              self.type_version)
