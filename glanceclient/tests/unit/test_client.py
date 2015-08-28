# Copyright 2014 Red Hat, Inc.
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

from glanceclient import client
from glanceclient import v1
from glanceclient import v2


class ClientTest(testtools.TestCase):

    def test_no_endpoint_error(self):
        self.assertRaises(ValueError, client.Client, None)

    def test_endpoint(self):
        gc = client.Client(1, "http://example.com")
        self.assertEqual("http://example.com", gc.http_client.endpoint)
        self.assertIsInstance(gc, v1.client.Client)

    def test_versioned_endpoint(self):
        gc = client.Client(1, "http://example.com/v2")
        self.assertEqual("http://example.com", gc.http_client.endpoint)
        self.assertIsInstance(gc, v1.client.Client)

    def test_versioned_endpoint_no_version(self):
        gc = client.Client(endpoint="http://example.com/v2")
        self.assertEqual("http://example.com", gc.http_client.endpoint)
        self.assertIsInstance(gc, v2.client.Client)

    def test_versioned_endpoint_with_minor_revision(self):
        gc = client.Client(2.2, "http://example.com/v2.1")
        self.assertEqual("http://example.com", gc.http_client.endpoint)
        self.assertIsInstance(gc, v2.client.Client)

    def test_endpoint_with_version_hostname(self):
        gc = client.Client(2, "http://v1.example.com")
        self.assertEqual("http://v1.example.com", gc.http_client.endpoint)
        self.assertIsInstance(gc, v2.client.Client)

    def test_versioned_endpoint_with_version_hostname_v2(self):
        gc = client.Client(endpoint="http://v1.example.com/v2")
        self.assertEqual("http://v1.example.com", gc.http_client.endpoint)
        self.assertIsInstance(gc, v2.client.Client)

    def test_versioned_endpoint_with_version_hostname_v1(self):
        gc = client.Client(endpoint="http://v2.example.com/v1")
        self.assertEqual("http://v2.example.com", gc.http_client.endpoint)
        self.assertIsInstance(gc, v1.client.Client)

    def test_versioned_endpoint_with_minor_revision_and_version_hostname(self):
        gc = client.Client(endpoint="http://v1.example.com/v2.1")
        self.assertEqual("http://v1.example.com", gc.http_client.endpoint)
        self.assertIsInstance(gc, v2.client.Client)
