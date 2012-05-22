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

import json


fixtures = {
    '/v1/images': {
        'POST': (
            {
                'location': '/v1/images/1',
            },
            json.dumps(
                {'image': {
                    'id': '1',
                    'name': 'image-1',
                    'container_format': 'ovf',
                    'disk_format': 'vhd',
                    'owner': 'asdf',
                    'size': '1024',
                    'min_ram': '512',
                    'min_disk': '10',
                    'properties': {'a': 'b', 'c': 'd'},
                }},
            ),
        ),
    },
    '/v1/images/detail': {
        'GET': (
            {},
            {'images': [
                {
                    'id': '1',
                    'name': 'image-1',
                    'properties': {'arch': 'x86_64'},
                },
            ]},
        ),
    },
    '/v1/images/1': {
        'HEAD': (
            {
                'x-image-meta-id': '1',
                'x-image-meta-name': 'image-1',
                'x-image-meta-property-arch': 'x86_64',
            },
            None),
        'PUT': (
            {},
            json.dumps(
                {'image': {
                    'id': '1',
                    'name': 'image-2',
                    'container_format': 'ovf',
                    'disk_format': 'vhd',
                    'owner': 'asdf',
                    'size': '1024',
                    'min_ram': '512',
                    'min_disk': '10',
                    'properties': {'a': 'b', 'c': 'd'},
                }},
            ),
        ),
        'DELETE': ({}, None),
    },
    '/v1/images/1/members': {
        'GET': (
            {},
            {'members': [
                {'member_id': '1', 'can_share': False},
            ]},
        ),
        'PUT': ({}, None),
    },
    '/v1/images/1/members/1': {
        'GET': (
            {},
            {'member': {
                'member_id': '1',
                'can_share': False,
            }},
        ),
        'PUT': ({}, None),
        'DELETE': ({}, None),
    },
    '/v1/shared-images/1': {
        'GET': (
            {},
            {'shared_images': [
                {'image_id': '1', 'can_share': False},
            ]},
        ),
    },
}


class FakeAPI(object):

    def __init__(self):
        self.calls = []

    def _request(self, method, url, headers=None, body=None):
        call = (method, url, headers or {}, body)
        self.calls.append(call)
        # drop any query params
        url = url.split('?', 1)[0]
        return fixtures[url][method]

    def raw_request(self, *args, **kwargs):
        return self._request(*args, **kwargs)

    def json_request(self, *args, **kwargs):
        return self._request(*args, **kwargs)
