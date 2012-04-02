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

fixtures = {
    '/v1/images': {
        'POST': (
            {
                'location': '/v1/images/1',
                'x-image-meta-id': '1',
                'x-image-meta-name': 'image-1',
                'x-image-meta-property-arch': 'x86_64',
            },
            None),
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
            {
                'x-image-meta-id': '1',
                'x-image-meta-name': 'image-2',
                'x-image-meta-property-arch': 'x86_64',
            },
            None),
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
    '/v1/shared_images/1': {
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

    def get(self, url):
        return self._request('GET', url)

    def head(self, url):
        return self._request('HEAD', url)

    def post(self, url, headers=None, body=None):
        return self._request('POST', url, headers, body)

    def put(self, url, headers=None, body=None):
        return self._request('PUT', url, headers, body)

    def delete(self, url):
        return self._request('DELETE', url)
