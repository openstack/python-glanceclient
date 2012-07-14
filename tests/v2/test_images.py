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

import unittest

import warlock

from glanceclient.v2 import images
from tests import utils


fixtures = {
    '/v2/images?limit=20': {
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
                'image': {
                    'id': '3a4560a1-e585-443e-9b39-553b46ec92d1',
                    'name': 'image-1',
                },
            },
        ),
    },
}


fake_schema = {'name': 'image', 'properties': {'id': {}, 'name': {}}}
FakeModel = warlock.model_factory(fake_schema)


class TestController(unittest.TestCase):
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

    def test_get_image(self):
        image = self.controller.get('3a4560a1-e585-443e-9b39-553b46ec92d1')
        self.assertEqual(image.id, '3a4560a1-e585-443e-9b39-553b46ec92d1')
        self.assertEqual(image.name, 'image-1')
