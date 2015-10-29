# Copyright 2015 OpenStack Foundation
# Copyright 2015 Huawei Corp.
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


class VersionController(object):
    def __init__(self, http_client):
        self.http_client = http_client

    def list(self):
        """List all versions."""
        url = '/versions'
        resp, body = self.http_client.get(url)
        return body.get('versions', None)
