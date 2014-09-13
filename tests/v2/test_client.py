# Copyright 2013 OpenStack LLC.
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

from glanceclient.v2 import client


class ClientTest(testtools.TestCase):

    def setUp(self):
        super(ClientTest, self).setUp()

    def tearDown(self):
        super(ClientTest, self).tearDown()

    def test_endpoint(self):
        gc = client.Client("http://example.com")
        self.assertEqual("http://example.com", gc.http_client.endpoint)

    def test_versioned_endpoint(self):
        gc = client.Client("http://example.com/v2")
        self.assertEqual("http://example.com", gc.http_client.endpoint)

    def test_versioned_endpoint_with_minor_revision(self):
        gc = client.Client("http://example.com/v2.1")
        self.assertEqual("http://example.com", gc.http_client.endpoint)
