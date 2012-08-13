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

import errno
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
                    'is_public': False,
                    'protected': False,
                    'deleted': False,
                }},
            ),
        ),
    },
    '/v1/images/detail?limit=20': {
        'GET': (
            {},
            {'images': [
                {
                    'id': 'a',
                    'name': 'image-1',
                    'properties': {'arch': 'x86_64'},
                },
                {
                    'id': 'b',
                    'name': 'image-2',
                    'properties': {'arch': 'x86_64'},
                },
            ]},
        ),
    },
    '/v1/images/detail?marker=a&limit=20': {
        'GET': (
            {},
            {'images': [
                {
                    'id': 'b',
                    'name': 'image-1',
                    'properties': {'arch': 'x86_64'},
                },
                {
                    'id': 'c',
                    'name': 'image-2',
                    'properties': {'arch': 'x86_64'},
                },
            ]},
        ),
    },
    '/v1/images/detail?limit=2': {
        'GET': (
            {},
            {'images': [
                {
                    'id': 'a',
                    'name': 'image-1',
                    'properties': {'arch': 'x86_64'},
                },
                {
                    'id': 'b',
                    'name': 'image-2',
                    'properties': {'arch': 'x86_64'},
                },
            ]},
        ),
    },
    '/v1/images/detail?marker=b&limit=2': {
        'GET': (
            {},
            {'images': [
                {
                    'id': 'c',
                    'name': 'image-3',
                    'properties': {'arch': 'x86_64'},
                },
            ]},
        ),
    },
    '/v1/images/detail?limit=20&name=foo': {
        'GET': (
            {},
            {'images': [
                {
                    'id': 'a',
                    'name': 'image-1',
                    'properties': {'arch': 'x86_64'},
                },
                {
                    'id': 'b',
                    'name': 'image-2',
                    'properties': {'arch': 'x86_64'},
                },
            ]},
        ),
    },
    '/v1/images/detail?property-ping=pong&limit=20': {
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
                'x-image-meta-is_public': 'false',
                'x-image-meta-protected': 'false',
                'x-image-meta-deleted': 'false',
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
                    'is_public': False,
                    'protected': False,
                }},
            ),
        ),
        'DELETE': ({}, None),
    },
    '/v1/images/2': {
       'HEAD': (
            {
                'x-image-meta-id': '2'
            },
            None,
        ),
        'GET': (
            {
                'x-image-meta-checksum': 'wrong'
            },
            'YYY',
        ),
    },
    '/v1/images/3': {
       'HEAD': (
            {
                'x-image-meta-id': '3'
            },
            None,
        ),
        'GET': (
            {
                'x-image-meta-checksum': '0745064918b49693cca64d6b6a13d28a'
            },
            'ZZZ',
        ),
    },
}


class ImageManagerTest(unittest.TestCase):

    def setUp(self):
        self.api = utils.FakeAPI(fixtures)
        self.mgr = glanceclient.v1.images.ImageManager(self.api)

    def test_paginated_list(self):
        images = list(self.mgr.list(page_size=2))
        expect = [
            ('GET', '/v1/images/detail?limit=2', {}, None),
            ('GET', '/v1/images/detail?marker=b&limit=2', {}, None),
        ]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(len(images), 3)
        self.assertEqual(images[0].id, 'a')
        self.assertEqual(images[1].id, 'b')
        self.assertEqual(images[2].id, 'c')

    def test_list_with_limit_less_than_page_size(self):
        list(self.mgr.list(page_size=20, limit=10))
        expect = [('GET', '/v1/images/detail?limit=20', {}, None)]
        self.assertEqual(self.api.calls, expect)

    def test_list_with_limit_greater_than_page_size(self):
        list(self.mgr.list(page_size=20, limit=30))
        expect = [('GET', '/v1/images/detail?limit=20', {}, None)]
        self.assertEqual(self.api.calls, expect)

    def test_list_with_marker(self):
        list(self.mgr.list(marker='a'))
        expect = [('GET', '/v1/images/detail?marker=a&limit=20', {}, None)]
        self.assertEqual(self.api.calls, expect)

    def test_list_with_filter(self):
        list(self.mgr.list(filters={'name': "foo"}))
        expect = [('GET', '/v1/images/detail?limit=20&name=foo', {}, None)]
        self.assertEqual(self.api.calls, expect)

    def test_list_with_property_filters(self):
        list(self.mgr.list(filters={'properties': {'ping': 'pong'}}))
        url = '/v1/images/detail?property-ping=pong&limit=20'
        expect = [('GET', url, {}, None)]
        self.assertEqual(self.api.calls, expect)

    def test_get(self):
        image = self.mgr.get('1')
        expect = [('HEAD', '/v1/images/1', {}, None)]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(image.id, '1')
        self.assertEqual(image.name, 'image-1')
        self.assertEqual(image.is_public, False)
        self.assertEqual(image.protected, False)
        self.assertEqual(image.deleted, False)

    def test_data(self):
        data = ''.join([b for b in self.mgr.data('1', do_checksum=False)])
        expect = [('GET', '/v1/images/1', {}, None)]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(data, 'XXX')

        expect += [('GET', '/v1/images/1', {}, None)]
        data = ''.join([b for b in self.mgr.data('1')])
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(data, 'XXX')

    def test_data_with_wrong_checksum(self):
        data = ''.join([b for b in self.mgr.data('2', do_checksum=False)])
        expect = [('GET', '/v1/images/2', {}, None)]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(data, 'YYY')

        expect += [('GET', '/v1/images/2', {}, None)]
        data = self.mgr.data('2')
        self.assertEqual(self.api.calls, expect)
        try:
            data = ''.join([b for b in data])
            self.fail('data did not raise an error.')
        except IOError, e:
            self.assertEqual(errno.EPIPE, e.errno)
            msg = 'was fd7c5c4fdaa97163ee4ba8842baa537a expected wrong'
            self.assertTrue(msg in str(e))

    def test_data_with_checksum(self):
        data = ''.join([b for b in self.mgr.data('3', do_checksum=False)])
        expect = [('GET', '/v1/images/3', {}, None)]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(data, 'ZZZ')

        expect += [('GET', '/v1/images/3', {}, None)]
        data = ''.join([b for b in self.mgr.data('3')])
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(data, 'ZZZ')

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
        self.assertEqual(image.size, 1024)
        self.assertEqual(image.min_ram, 512)
        self.assertEqual(image.min_disk, 10)
        self.assertEqual(image.is_public, False)
        self.assertEqual(image.protected, False)
        self.assertEqual(image.deleted, False)
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
            'deleted': False,
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
            'x-image-meta-deleted': 'False',
        }
        expect = [('PUT', '/v1/images/1', expect_hdrs, None)]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(image.id, '1')
        self.assertEqual(image.name, 'image-2')
        self.assertEqual(image.size, 1024)
        self.assertEqual(image.min_ram, 512)
        self.assertEqual(image.min_disk, 10)

    def test_update_with_data(self):
        image_data = StringIO.StringIO('XXX')
        self.mgr.update('1', data=image_data)
        expect_headers = {'x-image-meta-size': '3'}
        expect = [('PUT', '/v1/images/1', expect_headers, image_data)]
        self.assertEqual(self.api.calls, expect)

    def test_update_with_purge_props(self):
        self.mgr.update('1', purge_props=True)
        expect_headers = {'x-glance-registry-purge-props': 'true'}
        expect = [('PUT', '/v1/images/1', expect_headers, None)]
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
        data = ''.join([b for b in image.data()])
        expect = [
            ('HEAD', '/v1/images/1', {}, None),
            ('GET', '/v1/images/1', {}, None),
        ]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(data, 'XXX')

        data = ''.join([b for b in image.data(do_checksum=False)])
        expect += [('GET', '/v1/images/1', {}, None)]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(data, 'XXX')

    def test_data_with_wrong_checksum(self):
        image = self.mgr.get('2')
        data = ''.join([b for b in image.data(do_checksum=False)])
        expect = [
            ('HEAD', '/v1/images/2', {}, None),
            ('GET', '/v1/images/2', {}, None),
        ]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(data, 'YYY')

        data = image.data()
        expect += [('GET', '/v1/images/2', {}, None)]
        self.assertEqual(self.api.calls, expect)
        try:
            data = ''.join([b for b in image.data()])
            self.fail('data did not raise an error.')
        except IOError, e:
            self.assertEqual(errno.EPIPE, e.errno)
            msg = 'was fd7c5c4fdaa97163ee4ba8842baa537a expected wrong'
            self.assertTrue(msg in str(e))

    def test_data_with_checksum(self):
        image = self.mgr.get('3')
        data = ''.join([b for b in image.data(do_checksum=False)])
        expect = [
            ('HEAD', '/v1/images/3', {}, None),
            ('GET', '/v1/images/3', {}, None),
        ]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(data, 'ZZZ')

        data = ''.join([b for b in image.data()])
        expect += [('GET', '/v1/images/3', {}, None)]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(data, 'ZZZ')
