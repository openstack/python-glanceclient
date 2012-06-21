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
import StringIO
import unittest

import glanceclient.v1.images
from tests import utils


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
        'GET': (
            {},
            'XXX',
        ),
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

}


class ImageManagerTest(unittest.TestCase):

    def setUp(self):
        self.api = utils.FakeAPI(fixtures)
        self.mgr = glanceclient.v1.images.ImageManager(self.api)

    def test_list(self):
        images = self.mgr.list()
        expect = [('GET', '/v1/images/detail', {}, None)]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0].id, '1')
        self.assertEqual(images[0].name, 'image-1')
        self.assertEqual(images[0].properties, {'arch': 'x86_64'})

    def test_list_with_limit(self):
        self.mgr.list(limit=10)
        expect = [('GET', '/v1/images/detail?limit=10', {}, None)]
        self.assertEqual(self.api.calls, expect)

    def test_list_with_marker(self):
        self.mgr.list(marker=20)
        expect = [('GET', '/v1/images/detail?marker=20', {}, None)]
        self.assertEqual(self.api.calls, expect)

    def test_list_with_filter(self):
        self.mgr.list(filters={'name': "foo"})
        expect = [('GET', '/v1/images/detail?name=foo', {}, None)]
        self.assertEqual(self.api.calls, expect)

    def test_get(self):
        image = self.mgr.get('1')
        expect = [('HEAD', '/v1/images/1', {}, None)]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(image.id, '1')
        self.assertEqual(image.name, 'image-1')

    def test_data(self):
        data = self.mgr.data('1')
        expect = [('GET', '/v1/images/1', {}, None)]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(data, 'XXX')

    def test_delete(self):
        self.mgr.delete('1')
        expect = [('DELETE', '/v1/images/1', {}, None)]
        self.assertEqual(self.api.calls, expect)

    def test_create_without_data(self):
        params = {
            'id': '1',
            'name': 'image-1',
            'container_format': 'ovf',
            'disk_format': 'vhd',
            'owner': 'asdf',
            'size': 1024,
            'min_ram': 512,
            'min_disk': 10,
            'copy_from': 'http://example.com',
            'properties': {'a': 'b', 'c': 'd'},
        }
        image = self.mgr.create(**params)
        expect_headers = {
            'x-image-meta-id': '1',
            'x-image-meta-name': 'image-1',
            'x-image-meta-container_format': 'ovf',
            'x-image-meta-disk_format': 'vhd',
            'x-image-meta-owner': 'asdf',
            'x-image-meta-size': '1024',
            'x-image-meta-min_ram': '512',
            'x-image-meta-min_disk': '10',
            'x-glance-api-copy-from': 'http://example.com',
            'x-image-meta-property-a': 'b',
            'x-image-meta-property-c': 'd',
        }
        expect = [('POST', '/v1/images', expect_headers, None)]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(image.id, '1')
        self.assertEqual(image.name, 'image-1')
        self.assertEqual(image.container_format, 'ovf')
        self.assertEqual(image.disk_format, 'vhd')
        self.assertEqual(image.owner, 'asdf')
        self.assertEqual(image.size, '1024')
        self.assertEqual(image.min_ram, '512')
        self.assertEqual(image.min_disk, '10')
        self.assertEqual(image.properties, {'a': 'b', 'c': 'd'})

    def test_create_with_data(self):
        image_data = StringIO.StringIO('XXX')
        self.mgr.create(data=image_data)
        expect_headers = {'x-image-meta-size': '3'}
        expect = [('POST', '/v1/images', expect_headers, image_data)]
        self.assertEqual(self.api.calls, expect)

    def test_update(self):
        fields = {
            'name': 'image-2',
            'container_format': 'ovf',
            'disk_format': 'vhd',
            'owner': 'asdf',
            'size': 1024,
            'min_ram': 512,
            'min_disk': 10,
            'copy_from': 'http://example.com',
            'properties': {'a': 'b', 'c': 'd'},
        }
        image = self.mgr.update('1', **fields)
        expect_hdrs = {
            'x-image-meta-name': 'image-2',
            'x-image-meta-container_format': 'ovf',
            'x-image-meta-disk_format': 'vhd',
            'x-image-meta-owner': 'asdf',
            'x-image-meta-size': '1024',
            'x-image-meta-min_ram': '512',
            'x-image-meta-min_disk': '10',
            'x-glance-api-copy-from': 'http://example.com',
            'x-image-meta-property-a': 'b',
            'x-image-meta-property-c': 'd',
        }
        expect = [('PUT', '/v1/images/1', expect_hdrs, None)]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(image.id, '1')
        self.assertEqual(image.name, 'image-2')

    def test_update_with_data(self):
        image_data = StringIO.StringIO('XXX')
        self.mgr.update('1', data=image_data)
        expect_headers = {'x-image-meta-size': '3'}
        expect = [('PUT', '/v1/images/1', expect_headers, image_data)]
        self.assertEqual(self.api.calls, expect)


class ImageTest(unittest.TestCase):
    def setUp(self):
        self.api = utils.FakeAPI(fixtures)
        self.mgr = glanceclient.v1.images.ImageManager(self.api)

    def test_delete(self):
        image = self.mgr.get('1')
        image.delete()
        expect = [
            ('HEAD', '/v1/images/1', {}, None),
            ('DELETE', '/v1/images/1', {}, None),
        ]
        self.assertEqual(self.api.calls, expect)

    def test_update(self):
        image = self.mgr.get('1')
        image.update(name='image-5')
        expect = [
            ('HEAD', '/v1/images/1', {}, None),
            ('PUT', '/v1/images/1', {'x-image-meta-name': 'image-5'}, None),
        ]
        self.assertEqual(self.api.calls, expect)

    def test_data(self):
        image = self.mgr.get('1')
        data = image.data()
        expect = [
            ('HEAD', '/v1/images/1', {}, None),
            ('GET', '/v1/images/1', {}, None),
        ]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(data, 'XXX')
