# Copyright 2013 OpenStack Foundation
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


class Controller(object):
    def __init__(self, http_client, model):
        self.http_client = http_client
        self.model = model

    def list(self, image_id):
        url = '/v2/images/%s/members' % image_id
        resp, body = self.http_client.json_request('GET', url)
        for member in body['members']:
            yield self.model(member)

    def delete(self, image_id, member_id):
        self.http_client.json_request('DELETE',
                                      '/v2/images/%s/members/%s' %
                                      (image_id, member_id))

    def update(self, image_id, member_id, member_status):
        url = '/v2/images/%s/members/%s' % (image_id, member_id)
        body = {'status': member_status}
        resp, updated_member = self.http_client.json_request('PUT', url,
                                                             body=body)
        return self.model(updated_member)

    def create(self, image_id, member_id):
        url = '/v2/images/%s/members' % image_id
        body = {'member': member_id}
        resp, created_member = self.http_client.json_request('POST', url,
                                                             body=body)
        return self.model(created_member)
