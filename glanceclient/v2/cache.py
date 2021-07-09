# Copyright 2021 OpenStack Foundation
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

from glanceclient.common import utils
from glanceclient import exc

TARGET_VALUES = ('both', 'cache', 'queue')


class Controller(object):
    def __init__(self, http_client):
        self.http_client = http_client

    def is_supported(self, version):
        if utils.has_version(self.http_client, version):
            return True
        else:
            raise exc.HTTPNotImplemented(
                'Glance does not support image caching API (v2.14)')

    @utils.add_req_id_to_object()
    def list(self):
        if self.is_supported('v2.14'):
            url = '/v2/cache'
            resp, body = self.http_client.get(url)
            return body, resp

    @utils.add_req_id_to_object()
    def delete(self, image_id):
        if self.is_supported('v2.14'):
            resp, body = self.http_client.delete('/v2/cache/%s' %
                                                 image_id)
            return body, resp

    @utils.add_req_id_to_object()
    def clear(self, target):
        if self.is_supported('v2.14'):
            url = '/v2/cache'
            headers = {}
            if target != "both":
                headers = {'x-image-cache-clear-target': target}
            resp, body = self.http_client.delete(url, headers=headers)
            return body, resp

    @utils.add_req_id_to_object()
    def queue(self, image_id):
        if self.is_supported('v2.14'):
            url = '/v2/cache/%s' % image_id
            resp, body = self.http_client.put(url)
            return body, resp
