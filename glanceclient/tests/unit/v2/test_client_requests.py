# Copyright (c) 2015 OpenStack Foundation
# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from requests_mock.contrib import fixture as rm_fixture

from glanceclient import client
from glanceclient.tests.unit.v2.fixtures import image_create_fixture
from glanceclient.tests.unit.v2.fixtures import image_list_fixture
from glanceclient.tests.unit.v2.fixtures import image_show_fixture
from glanceclient.tests.unit.v2.fixtures import schema_fixture
from glanceclient.tests import utils as testutils
from glanceclient.v2.image_schema import _BASE_SCHEMA


DEFAULT_PAGE_SIZE = 200


class ClientTestRequests(testutils.TestCase):
    """Client tests using the requests mock library."""

    def test_list_bad_image_schema(self):
        # if kernel_id or ramdisk_id are not uuids, verify we can
        # still perform an image listing. Regression test for bug
        # 1477910
        self.requests = self.useFixture(rm_fixture.Fixture())
        self.requests.get('http://example.com/v2/schemas/image',
                          json=schema_fixture)
        self.requests.get('http://example.com/v2/images?'
                          f'limit={DEFAULT_PAGE_SIZE}',
                          json=image_list_fixture)
        gc = client.Client(2.2, "http://example.com/v2.1")
        images = gc.images.list()
        for image in images:
            pass

    def test_show_bad_image_schema(self):
        # if kernel_id or ramdisk_id are not uuids, verify we
        # don't fail due to schema validation
        self.requests = self.useFixture(rm_fixture.Fixture())
        self.requests.get('http://example.com/v2/schemas/image',
                          json=schema_fixture)
        self.requests.get('http://example.com/v2/images/%s'
                          % image_show_fixture['id'],
                          json=image_show_fixture)
        gc = client.Client(2.2, "http://example.com/v2.1")
        img = gc.images.get(image_show_fixture['id'])
        self.assertEqual(image_show_fixture['checksum'], img['checksum'])

    def test_invalid_disk_format(self):
        self.requests = self.useFixture(rm_fixture.Fixture())
        self.requests.get('http://example.com/v2/schemas/image',
                          json=_BASE_SCHEMA)
        self.requests.post('http://example.com/v2/images',
                           json=image_create_fixture)
        self.requests.get('http://example.com/v2/images/%s'
                          % image_show_fixture['id'],
                          json=image_show_fixture)
        gc = client.Client(2.2, "http://example.com/v2.1")
        fields = {"disk_format": "qbull2"}
        try:
            gc.images.create(**fields)
            self.fail("Failed to raise exception when using bad disk format")
        except TypeError:
            pass

    def test_valid_disk_format(self):
        self.requests = self.useFixture(rm_fixture.Fixture())
        self.requests.get('http://example.com/v2/schemas/image',
                          json=_BASE_SCHEMA)
        self.requests.post('http://example.com/v2/images',
                           json=image_create_fixture)
        self.requests.get('http://example.com/v2/images/%s'
                          % image_show_fixture['id'],
                          json=image_show_fixture)
        gc = client.Client(2.2, "http://example.com/v2.1")
        fields = {"disk_format": "vhdx"}
        gc.images.create(**fields)
