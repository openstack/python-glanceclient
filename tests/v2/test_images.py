# Copyright 2012 OpenStack Foundation.
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

import errno
import testtools

import warlock

from glanceclient.v2 import images
from tests import utils

_BOGUS_ID = '63e7f218-29de-4477-abdc-8db7c9533188'
_EVERYTHING_ID = '802cbbb7-0379-4c38-853f-37302b5e3d29'
_OWNED_IMAGE_ID = 'a4963502-acc7-42ba-ad60-5aa0962b7faf'
_OWNER_ID = '6bd473f0-79ae-40ad-a927-e07ec37b642f'
_PRIVATE_ID = 'e33560a7-3964-4de5-8339-5a24559f99ab'
_PUBLIC_ID = '857806e7-05b6-48e0-9d40-cb0e6fb727b9'
_SHARED_ID = '331ac905-2a38-44c5-a83d-653db8f08313'
_STATUS_REJECTED_ID = 'f3ea56ff-d7e4-4451-998c-1e3d33539c8e'

fixtures = {
    '/v2/images?limit=%d' % images.DEFAULT_PAGE_SIZE: {
        'GET': (
            {},
            {'images': [
                {
                    'id': '3a4560a1-e585-443e-9b39-553b46ec92d1',
                    'name': 'image-1',
                },
                {
                    'id': '6f99bf80-2ee6-47cf-acfe-1f1fabb7e810',
                    'name': 'image-2',
                },
            ]},
        ),
    },
    '/v2/images?limit=1': {
        'GET': (
            {},
            {
                'images': [
                    {
                        'id': '3a4560a1-e585-443e-9b39-553b46ec92d1',
                        'name': 'image-1',
                    },
                ],
                'next': ('/v2/images?limit=1&'
                         'marker=3a4560a1-e585-443e-9b39-553b46ec92d1'),
            },
        ),
    },
    ('/v2/images?limit=1&marker=3a4560a1-e585-443e-9b39-553b46ec92d1'): {
        'GET': (
            {},
            {'images': [
                {
                    'id': '6f99bf80-2ee6-47cf-acfe-1f1fabb7e810',
                    'name': 'image-2',
                },
            ]},
        ),
    },
    '/v2/images/3a4560a1-e585-443e-9b39-553b46ec92d1': {
        'GET': (
            {},
            {
                'id': '3a4560a1-e585-443e-9b39-553b46ec92d1',
                'name': 'image-1',
            },
        ),
        'PATCH': (
            {},
            '',
        ),
    },
    'v2/images/87b634c1-f893-33c9-28a9-e5673c99239a': {
        'DELETE': (
            {},
            {
                'id': '87b634c1-f893-33c9-28a9-e5673c99239a',
            },
        ),
    },
    '/v2/images/5cc4bebc-db27-11e1-a1eb-080027cbe205/file': {
        'GET': (
            {},
            'A',
        ),
    },
    '/v2/images/66fb18d6-db27-11e1-a1eb-080027cbe205/file': {
        'GET': (
            {
                'content-md5': 'wrong'
            },
            'BB',
        ),
    },
    '/v2/images/1b1c6366-dd57-11e1-af0f-02163e68b1d8/file': {
        'GET': (
            {
                'content-md5': 'defb99e69a9f1f6e06f15006b1f166ae'
            },
            'CCC',
        ),
    },
    '/v2/images?limit=%d&visibility=public' % images.DEFAULT_PAGE_SIZE: {
        'GET': (
            {},
            {'images': [
                {
                    'id': _PUBLIC_ID,
                    'harvey': 'lipshitz',
                },
            ]},
        ),
    },
    '/v2/images?limit=%d&visibility=private' % images.DEFAULT_PAGE_SIZE: {
        'GET': (
            {},
            {'images': [
                {
                    'id': _PRIVATE_ID,
                },
            ]},
        ),
    },
    '/v2/images?limit=%d&visibility=shared' % images.DEFAULT_PAGE_SIZE: {
        'GET': (
            {},
            {'images': [
                {
                    'id': _SHARED_ID,
                },
            ]},
        ),
    },
    '/v2/images?limit=%d&member_status=rejected' % images.DEFAULT_PAGE_SIZE: {
        'GET': (
            {},
            {'images': [
                {
                    'id': _STATUS_REJECTED_ID,
                },
            ]},
        ),
    },
    '/v2/images?limit=%d&member_status=pending' % images.DEFAULT_PAGE_SIZE: {
        'GET': (
            {},
            {'images': []},
        ),
    },
    '/v2/images?owner=%s&limit=%d' % (_OWNER_ID, images.DEFAULT_PAGE_SIZE): {
        'GET': (
            {},
            {'images': [
                {
                    'id': _OWNED_IMAGE_ID,
                },
            ]},
        ),
    },
    '/v2/images?owner=%s&limit=%d' % (_BOGUS_ID, images.DEFAULT_PAGE_SIZE): {
        'GET': (
            {},
            {'images': []},
        ),
    },
    '/v2/images?owner=%s&limit=%d&member_status=pending&visibility=shared'
    % (_BOGUS_ID, images.DEFAULT_PAGE_SIZE): {
        'GET': (
            {},
            {'images': [
                {
                    'id': _EVERYTHING_ID,
                },
            ]},
        ),
    },
}


fake_schema = {'name': 'image', 'properties': {'id': {}, 'name': {}}}
FakeModel = warlock.model_factory(fake_schema)


class TestController(testtools.TestCase):
    def setUp(self):
        super(TestController, self).setUp()
        self.api = utils.FakeAPI(fixtures)
        self.controller = images.Controller(self.api, FakeModel)

    def test_list_images(self):
        #NOTE(bcwaldon): cast to list since the controller returns a generator
        images = list(self.controller.list())
        self.assertEqual(images[0].id, '3a4560a1-e585-443e-9b39-553b46ec92d1')
        self.assertEqual(images[0].name, 'image-1')
        self.assertEqual(images[1].id, '6f99bf80-2ee6-47cf-acfe-1f1fabb7e810')
        self.assertEqual(images[1].name, 'image-2')

    def test_list_images_paginated(self):
        #NOTE(bcwaldon): cast to list since the controller returns a generator
        images = list(self.controller.list(page_size=1))
        self.assertEqual(images[0].id, '3a4560a1-e585-443e-9b39-553b46ec92d1')
        self.assertEqual(images[0].name, 'image-1')
        self.assertEqual(images[1].id, '6f99bf80-2ee6-47cf-acfe-1f1fabb7e810')
        self.assertEqual(images[1].name, 'image-2')

    def test_list_images_visibility_public(self):
        filters = {'filters': dict([('visibility', 'public')])}
        images = list(self.controller.list(**filters))
        self.assertEqual(images[0].id, _PUBLIC_ID)

    def test_list_images_visibility_private(self):
        filters = {'filters': dict([('visibility', 'private')])}
        images = list(self.controller.list(**filters))
        self.assertEqual(images[0].id, _PRIVATE_ID)

    def test_list_images_visibility_shared(self):
        filters = {'filters': dict([('visibility', 'shared')])}
        images = list(self.controller.list(**filters))
        self.assertEqual(images[0].id, _SHARED_ID)

    def test_list_images_member_status_rejected(self):
        filters = {'filters': dict([('member_status', 'rejected')])}
        images = list(self.controller.list(**filters))
        self.assertEqual(images[0].id, _STATUS_REJECTED_ID)

    def test_list_images_for_owner(self):
        filters = {'filters': dict([('owner', _OWNER_ID)])}
        images = list(self.controller.list(**filters))
        self.assertEqual(images[0].id, _OWNED_IMAGE_ID)

    def test_list_images_for_bogus_owner(self):
        filters = {'filters': dict([('owner', _BOGUS_ID)])}
        images = list(self.controller.list(**filters))
        self.assertEqual(images, [])

    def test_list_images_for_bunch_of_filters(self):
        filters = {'filters': dict([('owner', _BOGUS_ID),
                                    ('visibility', 'shared'),
                                    ('member_status', 'pending')])}
        images = list(self.controller.list(**filters))
        self.assertEqual(images[0].id, _EVERYTHING_ID)

    def test_get_image(self):
        image = self.controller.get('3a4560a1-e585-443e-9b39-553b46ec92d1')
        self.assertEqual(image.id, '3a4560a1-e585-443e-9b39-553b46ec92d1')
        self.assertEqual(image.name, 'image-1')

    def test_delete_image(self):
        self.controller.delete('87b634c1-f893-33c9-28a9-e5673c99239a')
        expect = [
            ('DELETE',
                'v2/images/87b634c1-f893-33c9-28a9-e5673c99239a',
                {},
                None)]
        self.assertEqual(self.api.calls, expect)

    def test_data_without_checksum(self):
        body = self.controller.data('5cc4bebc-db27-11e1-a1eb-080027cbe205',
                                    do_checksum=False)
        body = ''.join([b for b in body])
        self.assertEqual(body, 'A')

        body = self.controller.data('5cc4bebc-db27-11e1-a1eb-080027cbe205')
        body = ''.join([b for b in body])
        self.assertEqual(body, 'A')

    def test_data_with_wrong_checksum(self):
        body = self.controller.data('66fb18d6-db27-11e1-a1eb-080027cbe205',
                                    do_checksum=False)
        body = ''.join([b for b in body])
        self.assertEqual(body, 'BB')

        body = self.controller.data('66fb18d6-db27-11e1-a1eb-080027cbe205')
        try:
            body = ''.join([b for b in body])
            self.fail('data did not raise an error.')
        except IOError as e:
            self.assertEqual(errno.EPIPE, e.errno)
            msg = 'was 9d3d9048db16a7eee539e93e3618cbe7 expected wrong'
            self.assertTrue(msg in str(e))

    def test_data_with_checksum(self):
        body = self.controller.data('1b1c6366-dd57-11e1-af0f-02163e68b1d8',
                                    do_checksum=False)
        body = ''.join([b for b in body])
        self.assertEqual(body, 'CCC')

        body = self.controller.data('1b1c6366-dd57-11e1-af0f-02163e68b1d8')
        body = ''.join([b for b in body])
        self.assertEqual(body, 'CCC')

    def test_update_without_data(self):
        image_id = '3a4560a1-e585-443e-9b39-553b46ec92d1'
        params = {'name': 'pong'}
        image = self.controller.update(image_id, **params)
        expect_hdrs = {
            'Content-Type': 'application/openstack-images-v2.0-json-patch',
        }
        expect_body = '[{"path": "/name", "value": "pong", "op": "replace"}]'
        expect = [
            ('GET', '/v2/images/%s' % image_id, {}, None),
            ('PATCH', '/v2/images/%s' % image_id, expect_hdrs, expect_body),
            ('GET', '/v2/images/%s' % image_id, {}, None),
        ]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(image.id, image_id)
        #NOTE(bcwaldon): due to limitations of our fake api framework, the name
        # will not actually change - yet in real life it will...
        self.assertEqual(image.name, 'image-1')
