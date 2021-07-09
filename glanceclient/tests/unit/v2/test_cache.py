# Copyright 2021 Red Hat Inc.
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

import testtools
from unittest import mock

from glanceclient.common import utils as common_utils
from glanceclient import exc
from glanceclient.tests import utils
from glanceclient.v2 import cache


data_fixtures = {
    '/v2/cache': {
        'GET': (
            {},
            {
                'cached_images': [
                    {
                        'id': 'b0aa672a-bc26-4fcb-8be1-f53ca361943d',
                        'Last Accessed (UTC)': '2021-08-09T07:08:20.214543',
                        'Last Modified (UTC)': '2021-08-09T07:08:20.214543',
                        'Size': 13267968,
                        'Hits': 0
                    },
                    {
                        'id': 'df601a47-7251-4d20-84ae-07de335af424',
                        'Last Accessed (UTC)': '2021-08-09T07:08:20.214543',
                        'Last Modified (UTC)': '2021-08-09T07:08:20.214543',
                        'Size': 13267968,
                        'Hits': 0
                    },
                ],
                'queued_images': [
                    '3a4560a1-e585-443e-9b39-553b46ec92d1',
                    '6f99bf80-2ee6-47cf-acfe-1f1fabb7e810'
                ],
            },
        ),
        'DELETE': (
            {},
            '',
        ),
    },
    '/v2/cache/3a4560a1-e585-443e-9b39-553b46ec92d1': {
        'PUT': (
            {},
            '',
        ),
        'DELETE': (
            {},
            '',
        ),
    },
}


class TestCacheController(testtools.TestCase):
    def setUp(self):
        super(TestCacheController, self).setUp()
        self.api = utils.FakeAPI(data_fixtures)
        self.controller = cache.Controller(self.api)

    @mock.patch.object(common_utils, 'has_version')
    def test_list_cached(self, mock_has_version):
        mock_has_version.return_value = True
        images = self.controller.list()
        # Verify that we have 2 cached and 2 queued images
        self.assertEqual(2, len(images['cached_images']))
        self.assertEqual(2, len(images['queued_images']))

    @mock.patch.object(common_utils, 'has_version')
    def test_list_cached_empty_response(self, mock_has_version):
        dummy_fixtures = {
            '/v2/cache': {
                'GET': (
                    {},
                    {
                        'cached_images': [],
                        'queued_images': [],
                    },
                ),
            }
        }
        dummy_api = utils.FakeAPI(dummy_fixtures)
        dummy_controller = cache.Controller(dummy_api)
        mock_has_version.return_value = True
        images = dummy_controller.list()
        # Verify that we have 0 cached and 0 queued images
        self.assertEqual(0, len(images['cached_images']))
        self.assertEqual(0, len(images['queued_images']))

    @mock.patch.object(common_utils, 'has_version')
    def test_queue_image(self, mock_has_version):
        mock_has_version.return_value = True
        image_id = '3a4560a1-e585-443e-9b39-553b46ec92d1'
        self.controller.queue(image_id)
        expect = [('PUT', '/v2/cache/%s' % image_id,
                   {}, None)]
        self.assertEqual(expect, self.api.calls)

    @mock.patch.object(common_utils, 'has_version')
    def test_cache_clear_with_header(self, mock_has_version):
        mock_has_version.return_value = True
        self.controller.clear("cache")
        expect = [('DELETE', '/v2/cache',
                   {'x-image-cache-clear-target': 'cache'}, None)]
        self.assertEqual(expect, self.api.calls)

    @mock.patch.object(common_utils, 'has_version')
    def test_cache_delete(self, mock_has_version):
        mock_has_version.return_value = True
        image_id = '3a4560a1-e585-443e-9b39-553b46ec92d1'
        self.controller.delete(image_id)
        expect = [('DELETE', '/v2/cache/%s' % image_id,
                   {}, None)]
        self.assertEqual(expect, self.api.calls)

    @mock.patch.object(common_utils, 'has_version')
    def test_cache_not_supported(self, mock_has_version):
        mock_has_version.return_value = False
        self.assertRaises(exc.HTTPNotImplemented,
                          self.controller.list)
