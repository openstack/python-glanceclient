# Copyright 2012 OpenStack Foundation
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
import io
import json
import testtools
from urllib import parse

from glanceclient.tests import utils
from glanceclient.v1 import client
from glanceclient.v1 import images
from glanceclient.v1 import shell


DEFAULT_PAGE_SIZE = 20


fixtures = {
    '/v1/images': {
        'POST': (
            {
                'location': '/v1/images/1',
                'x-openstack-request-id': 'req-1234',
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
    f'/v1/images/detail?is_public=None&limit={DEFAULT_PAGE_SIZE}': {
        'GET': (
            {'x-openstack-request-id': 'req-1234'},
            {'images': [
                {
                    'id': 'a',
                    'owner': 'A',
                    'is_public': 'True',
                    'name': 'image-1',
                    'properties': {'arch': 'x86_64'},
                },
                {
                    'id': 'b',
                    'owner': 'B',
                    'is_public': 'False',
                    'name': 'image-2',
                    'properties': {'arch': 'x86_64'},
                },
                {
                    'id': 'c',
                    'is_public': 'False',
                    'name': 'image-3',
                    'properties': {'arch': 'x86_64'},
                },
            ]},
        ),
    },
    '/v1/images/detail?is_public=None&limit=5': {
        'GET': (
            {},
            {'images': [
                {
                    'id': 'a',
                    'owner': 'A',
                    'name': 'image-1',
                    'properties': {'arch': 'x86_64'},
                },
                {
                    'id': 'b',
                    'owner': 'B',
                    'name': 'image-2',
                    'properties': {'arch': 'x86_64'},
                },
                {
                    'id': 'b2',
                    'owner': 'B',
                    'name': 'image-3',
                    'properties': {'arch': 'x86_64'},
                },
                {
                    'id': 'c',
                    'name': 'image-3',
                    'properties': {'arch': 'x86_64'},
                },
            ]},
        ),
    },
    '/v1/images/detail?limit=5': {
        'GET': (
            {},
            {'images': [
                {
                    'id': 'a',
                    'owner': 'A',
                    'is_public': 'False',
                    'name': 'image-1',
                    'properties': {'arch': 'x86_64'},
                },
                {
                    'id': 'b',
                    'owner': 'A',
                    'is_public': 'False',
                    'name': 'image-2',
                    'properties': {'arch': 'x86_64'},
                },
                {
                    'id': 'b2',
                    'owner': 'B',
                    'name': 'image-3',
                    'properties': {'arch': 'x86_64'},
                },
                {
                    'id': 'c',
                    'is_public': 'True',
                    'name': 'image-3',
                    'properties': {'arch': 'x86_64'},
                },
            ]},
        ),
    },
    f'/v1/images/detail?limit={DEFAULT_PAGE_SIZE}&marker=a': {
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
    '/v1/images/detail?limit=1': {
        'GET': (
            {},
            {'images': [
                {
                    'id': 'a',
                    'name': 'image-0',
                    'properties': {'arch': 'x86_64'},
                },
            ]},
        ),
    },
    '/v1/images/detail?limit=1&marker=a': {
        'GET': (
            {},
            {'images': [
                {
                    'id': 'b',
                    'name': 'image-1',
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
    '/v1/images/detail?limit=2&marker=b': {
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
    f'/v1/images/detail?limit={DEFAULT_PAGE_SIZE}&name=foo': {
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
    f'/v1/images/detail?limit={DEFAULT_PAGE_SIZE}&property-ping=pong':
    {
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
    f'/v1/images/detail?limit={DEFAULT_PAGE_SIZE}&sort_dir=desc': {
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
    f'/v1/images/detail?limit={DEFAULT_PAGE_SIZE}&sort_key=name': {
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
                'x-image-meta-id': '3',
                'x-image-meta-name': u"ni\xf1o"
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
    '/v1/images/4': {
        'HEAD': (
            {
                'x-image-meta-id': '4',
                'x-image-meta-name': 'image-4',
                'x-image-meta-property-arch': 'x86_64',
                'x-image-meta-is_public': 'false',
                'x-image-meta-protected': 'false',
                'x-image-meta-deleted': 'false',
                'x-openstack-request-id': 'req-1234',
            },
            None),
        'GET': (
            {
                'x-openstack-request-id': 'req-1234',
            },
            'XXX',
        ),
        'PUT': (
            {
                'x-openstack-request-id': 'req-1234',
            },
            json.dumps(
                {'image': {
                    'id': '4',
                    'name': 'image-4',
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
        'DELETE': (
            {
                'x-openstack-request-id': 'req-1234',
            },
            None),
    },
    '/v1/images/v2_created_img': {
        'PUT': (
            {},
            json.dumps({
                "image": {
                    "status": "queued",
                    "deleted": False,
                    "container_format": "bare",
                    "min_ram": 0,
                    "updated_at": "2013-12-20T01:51:45",
                    "owner": "foo",
                    "min_disk": 0,
                    "is_public": False,
                    "deleted_at": None,
                    "id": "v2_created_img",
                    "size": None,
                    "name": "bar",
                    "checksum": None,
                    "created_at": "2013-12-20T01:50:38",
                    "disk_format": "qcow2",
                    "properties": {},
                    "protected": False
                }
            })
        ),
    },
}


class ImageManagerTest(testtools.TestCase):

    def setUp(self):
        super(ImageManagerTest, self).setUp()
        self.api = utils.FakeAPI(fixtures)
        self.mgr = images.ImageManager(self.api)

    def test_paginated_list(self):
        images = list(self.mgr.list(page_size=2))
        expect = [
            ('GET', '/v1/images/detail?limit=2', {}, None),
            ('GET', '/v1/images/detail?limit=2&marker=b', {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(3, len(images))
        self.assertEqual('a', images[0].id)
        self.assertEqual('b', images[1].id)
        self.assertEqual('c', images[2].id)

    def test_list_with_limit_less_than_page_size(self):
        results = list(self.mgr.list(page_size=2, limit=1))
        expect = [('GET', '/v1/images/detail?limit=2', {}, None)]
        self.assertEqual(1, len(results))
        self.assertEqual(expect, self.api.calls)

    def test_list_with_limit_greater_than_page_size(self):
        images = list(self.mgr.list(page_size=1, limit=2))
        expect = [
            ('GET', '/v1/images/detail?limit=1', {}, None),
            ('GET', '/v1/images/detail?limit=1&marker=a', {}, None),
        ]
        self.assertEqual(2, len(images))
        self.assertEqual('a', images[0].id)
        self.assertEqual('b', images[1].id)
        self.assertEqual(expect, self.api.calls)

    def test_list_with_marker(self):
        list(self.mgr.list(marker='a'))
        url = f'/v1/images/detail?limit={DEFAULT_PAGE_SIZE}&marker=a'
        expect = [('GET', url, {}, None)]
        self.assertEqual(expect, self.api.calls)

    def test_list_with_filter(self):
        list(self.mgr.list(filters={'name': "foo"}))
        url = f'/v1/images/detail?limit={DEFAULT_PAGE_SIZE}&name=foo'
        expect = [('GET', url, {}, None)]
        self.assertEqual(expect, self.api.calls)

    def test_list_with_property_filters(self):
        list(self.mgr.list(filters={'properties': {'ping': 'pong'}}))
        url = f'/v1/images/detail?limit={DEFAULT_PAGE_SIZE}&property-ping=pong'
        expect = [('GET', url, {}, None)]
        self.assertEqual(expect, self.api.calls)

    def test_list_with_sort_dir(self):
        list(self.mgr.list(sort_dir='desc'))
        url = f'/v1/images/detail?limit={DEFAULT_PAGE_SIZE}&sort_dir=desc'
        expect = [('GET', url, {}, None)]
        self.assertEqual(expect, self.api.calls)

    def test_list_with_sort_key(self):
        list(self.mgr.list(sort_key='name'))
        url = f'/v1/images/detail?limit={DEFAULT_PAGE_SIZE}&sort_key=name'
        expect = [('GET', url, {}, None)]
        self.assertEqual(expect, self.api.calls)

    def test_get(self):
        image = self.mgr.get('1')
        expect = [('HEAD', '/v1/images/1', {}, None)]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual('1', image.id)
        self.assertEqual('image-1', image.name)
        self.assertEqual(False, image.is_public)
        self.assertEqual(False, image.protected)
        self.assertEqual(False, image.deleted)
        self.assertEqual({'arch': 'x86_64'}, image.properties)

    def test_get_int(self):
        image = self.mgr.get(1)
        expect = [('HEAD', '/v1/images/1', {}, None)]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual('1', image.id)
        self.assertEqual('image-1', image.name)
        self.assertEqual(False, image.is_public)
        self.assertEqual(False, image.protected)
        self.assertEqual(False, image.deleted)
        self.assertEqual({'arch': 'x86_64'}, image.properties)

    def test_get_encoding(self):
        image = self.mgr.get('3')
        self.assertEqual(u"ni\xf1o", image.name)

    def test_get_req_id(self):
        params = {'return_req_id': []}
        self.mgr.get('4', **params)
        expect_req_id = ['req-1234']
        self.assertEqual(expect_req_id, params['return_req_id'])

    def test_data(self):
        data = ''.join([b for b in self.mgr.data('1', do_checksum=False)])
        expect = [('GET', '/v1/images/1', {}, None)]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual('XXX', data)

        expect += [('GET', '/v1/images/1', {}, None)]
        data = ''.join([b for b in self.mgr.data('1')])
        self.assertEqual(expect, self.api.calls)
        self.assertEqual('XXX', data)

    def test_data_with_wrong_checksum(self):
        data = ''.join([b for b in self.mgr.data('2', do_checksum=False)])
        expect = [('GET', '/v1/images/2', {}, None)]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual('YYY', data)

        expect += [('GET', '/v1/images/2', {}, None)]
        data = self.mgr.data('2')
        self.assertEqual(expect, self.api.calls)
        try:
            data = ''.join([b for b in data])
            self.fail('data did not raise an error.')
        except IOError as e:
            self.assertEqual(errno.EPIPE, e.errno)
            msg = 'was fd7c5c4fdaa97163ee4ba8842baa537a expected wrong'
            self.assertIn(msg, str(e))

    def test_data_req_id(self):
        params = {
            'do_checksum': False,
            'return_req_id': [],
        }
        ''.join([b for b in self.mgr.data('4', **params)])
        expect_req_id = ['req-1234']
        self.assertEqual(expect_req_id, params['return_req_id'])

    def test_data_with_checksum(self):
        data = ''.join([b for b in self.mgr.data('3', do_checksum=False)])
        expect = [('GET', '/v1/images/3', {}, None)]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual('ZZZ', data)

        expect += [('GET', '/v1/images/3', {}, None)]
        data = ''.join([b for b in self.mgr.data('3')])
        self.assertEqual(expect, self.api.calls)
        self.assertEqual('ZZZ', data)

    def test_delete(self):
        self.mgr.delete('1')
        expect = [('DELETE', '/v1/images/1', {}, None)]
        self.assertEqual(expect, self.api.calls)

    def test_delete_req_id(self):
        params = {
            'return_req_id': []
        }
        self.mgr.delete('4', **params)
        expect = [('DELETE', '/v1/images/4', {}, None)]
        self.assertEqual(self.api.calls, expect)
        expect_req_id = ['req-1234']
        self.assertEqual(expect_req_id, params['return_req_id'])

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
        self.assertEqual(expect, self.api.calls)
        self.assertEqual('1', image.id)
        self.assertEqual('image-1', image.name)
        self.assertEqual('ovf', image.container_format)
        self.assertEqual('vhd', image.disk_format)
        self.assertEqual('asdf', image.owner)
        self.assertEqual(1024, image.size)
        self.assertEqual(512, image.min_ram)
        self.assertEqual(10, image.min_disk)
        self.assertEqual(False, image.is_public)
        self.assertEqual(False, image.protected)
        self.assertEqual(False, image.deleted)
        self.assertEqual({'a': 'b', 'c': 'd'}, image.properties)

    def test_create_with_data(self):
        image_data = io.StringIO('XXX')
        self.mgr.create(data=image_data)
        expect_headers = {'x-image-meta-size': '3'}
        expect = [('POST', '/v1/images', expect_headers, image_data)]
        self.assertEqual(expect, self.api.calls)

    def test_create_req_id(self):
        params = {
            'id': '4',
            'name': 'image-4',
            'container_format': 'ovf',
            'disk_format': 'vhd',
            'owner': 'asdf',
            'size': 1024,
            'min_ram': 512,
            'min_disk': 10,
            'copy_from': 'http://example.com',
            'properties': {'a': 'b', 'c': 'd'},
            'return_req_id': [],
        }
        image = self.mgr.create(**params)
        expect_headers = {
            'x-image-meta-id': '4',
            'x-image-meta-name': 'image-4',
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
        self.assertEqual(expect, self.api.calls)
        self.assertEqual('1', image.id)
        expect_req_id = ['req-1234']
        self.assertEqual(expect_req_id, params['return_req_id'])

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
            'x-glance-registry-purge-props': 'false',
        }
        expect = [('PUT', '/v1/images/1', expect_hdrs, None)]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual('1', image.id)
        self.assertEqual('image-2', image.name)
        self.assertEqual(1024, image.size)
        self.assertEqual(512, image.min_ram)
        self.assertEqual(10, image.min_disk)

    def test_update_with_data(self):
        image_data = io.StringIO('XXX')
        self.mgr.update('1', data=image_data)
        expect_headers = {'x-image-meta-size': '3',
                          'x-glance-registry-purge-props': 'false'}
        expect = [('PUT', '/v1/images/1', expect_headers, image_data)]
        self.assertEqual(expect, self.api.calls)

    def test_update_with_purge_props(self):
        self.mgr.update('1', purge_props=True)
        expect_headers = {'x-glance-registry-purge-props': 'true'}
        expect = [('PUT', '/v1/images/1', expect_headers, None)]
        self.assertEqual(expect, self.api.calls)

    def test_update_with_purge_props_false(self):
        self.mgr.update('1', purge_props=False)
        expect_headers = {'x-glance-registry-purge-props': 'false'}
        expect = [('PUT', '/v1/images/1', expect_headers, None)]
        self.assertEqual(expect, self.api.calls)

    def test_update_req_id(self):
        fields = {
            'purge_props': True,
            'return_req_id': [],
        }
        self.mgr.update('4', **fields)
        expect_headers = {'x-glance-registry-purge-props': 'true'}
        expect = [('PUT', '/v1/images/4', expect_headers, None)]
        self.assertEqual(expect, self.api.calls)
        expect_req_id = ['req-1234']
        self.assertEqual(expect_req_id, fields['return_req_id'])

    def test_image_meta_from_headers_encoding(self):
        value = u"ni\xf1o"
        fields = {"x-image-meta-name": value}
        headers = self.mgr._image_meta_from_headers(fields)
        self.assertEqual(value, headers["name"])

    def test_image_list_with_owner(self):
        images = self.mgr.list(owner='A', page_size=DEFAULT_PAGE_SIZE)
        image_list = list(images)
        self.assertEqual('A', image_list[0].owner)
        self.assertEqual('a', image_list[0].id)
        self.assertEqual(1, len(image_list))

    def test_image_list_with_owner_req_id(self):
        fields = {
            'owner': 'A',
            'return_req_id': [],
        }
        images = self.mgr.list(**fields)
        next(images)
        self.assertEqual(['req-1234'], fields['return_req_id'])

    def test_image_list_with_notfound_owner(self):
        images = self.mgr.list(owner='X', page_size=DEFAULT_PAGE_SIZE)
        self.assertEqual(0, len(list(images)))

    def test_image_list_with_empty_string_owner(self):
        images = self.mgr.list(owner='', page_size=DEFAULT_PAGE_SIZE)
        image_list = list(images)
        self.assertRaises(AttributeError, lambda: image_list[0].owner)
        self.assertEqual('c', image_list[0].id)
        self.assertEqual(1, len(image_list))

    def test_image_list_with_unspecified_owner(self):
        images = self.mgr.list(owner=None, page_size=5)
        image_list = list(images)
        self.assertEqual('A', image_list[0].owner)
        self.assertEqual('a', image_list[0].id)
        self.assertEqual('A', image_list[1].owner)
        self.assertEqual('b', image_list[1].id)
        self.assertEqual('B', image_list[2].owner)
        self.assertEqual('b2', image_list[2].id)
        self.assertRaises(AttributeError, lambda: image_list[3].owner)
        self.assertEqual('c', image_list[3].id)
        self.assertEqual(4, len(image_list))

    def test_image_list_with_owner_and_limit(self):
        images = self.mgr.list(owner='B', page_size=5, limit=1)
        image_list = list(images)
        self.assertEqual('B', image_list[0].owner)
        self.assertEqual('b', image_list[0].id)
        self.assertEqual(1, len(image_list))

    def test_image_list_all_tenants(self):
        images = self.mgr.list(is_public=None, page_size=5)
        image_list = list(images)
        self.assertEqual('A', image_list[0].owner)
        self.assertEqual('a', image_list[0].id)
        self.assertEqual('B', image_list[1].owner)
        self.assertEqual('b', image_list[1].id)
        self.assertEqual('B', image_list[2].owner)
        self.assertEqual('b2', image_list[2].id)
        self.assertRaises(AttributeError, lambda: image_list[3].owner)
        self.assertEqual('c', image_list[3].id)
        self.assertEqual(4, len(image_list))

    def test_update_v2_created_image_using_v1(self):
        fields_to_update = {
            'name': 'bar',
            'container_format': 'bare',
            'disk_format': 'qcow2',
        }
        image = self.mgr.update('v2_created_img', **fields_to_update)
        expect_hdrs = {
            'x-image-meta-name': 'bar',
            'x-image-meta-container_format': 'bare',
            'x-image-meta-disk_format': 'qcow2',
            'x-glance-registry-purge-props': 'false',
        }
        expect = [('PUT', '/v1/images/v2_created_img', expect_hdrs, None)]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual('v2_created_img', image.id)
        self.assertEqual('bar', image.name)
        self.assertEqual(0, image.size)
        self.assertEqual('bare', image.container_format)
        self.assertEqual('qcow2', image.disk_format)


class ImageTest(testtools.TestCase):
    def setUp(self):
        super(ImageTest, self).setUp()
        self.api = utils.FakeAPI(fixtures)
        self.mgr = images.ImageManager(self.api)

    def test_delete(self):
        image = self.mgr.get('1')
        image.delete()
        expect = [
            ('HEAD', '/v1/images/1', {}, None),
            ('HEAD', '/v1/images/1', {}, None),
            ('DELETE', '/v1/images/1', {}, None),
        ]
        self.assertEqual(expect, self.api.calls)

    def test_update(self):
        image = self.mgr.get('1')
        image.update(name='image-5')
        expect = [
            ('HEAD', '/v1/images/1', {}, None),
            ('HEAD', '/v1/images/1', {}, None),
            ('PUT', '/v1/images/1',
             {'x-image-meta-name': 'image-5',
              'x-glance-registry-purge-props': 'false'}, None),
        ]
        self.assertEqual(expect, self.api.calls)

    def test_data(self):
        image = self.mgr.get('1')
        data = ''.join([b for b in image.data()])
        expect = [
            ('HEAD', '/v1/images/1', {}, None),
            ('HEAD', '/v1/images/1', {}, None),
            ('GET', '/v1/images/1', {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual('XXX', data)

        data = ''.join([b for b in image.data(do_checksum=False)])
        expect += [('GET', '/v1/images/1', {}, None)]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual('XXX', data)

    def test_data_with_wrong_checksum(self):
        image = self.mgr.get('2')
        data = ''.join([b for b in image.data(do_checksum=False)])
        expect = [
            ('HEAD', '/v1/images/2', {}, None),
            ('HEAD', '/v1/images/2', {}, None),
            ('GET', '/v1/images/2', {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual('YYY', data)

        data = image.data()
        expect += [('GET', '/v1/images/2', {}, None)]
        self.assertEqual(expect, self.api.calls)
        try:
            data = ''.join([b for b in image.data()])
            self.fail('data did not raise an error.')
        except IOError as e:
            self.assertEqual(errno.EPIPE, e.errno)
            msg = 'was fd7c5c4fdaa97163ee4ba8842baa537a expected wrong'
            self.assertIn(msg, str(e))

    def test_data_with_checksum(self):
        image = self.mgr.get('3')
        data = ''.join([b for b in image.data(do_checksum=False)])
        expect = [
            ('HEAD', '/v1/images/3', {}, None),
            ('HEAD', '/v1/images/3', {}, None),
            ('GET', '/v1/images/3', {}, None),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual('ZZZ', data)

        data = ''.join([b for b in image.data()])
        expect += [('GET', '/v1/images/3', {}, None)]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual('ZZZ', data)


class ParameterFakeAPI(utils.FakeAPI):
    image_list = {'images': [
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
    ]}

    def get(self, url, **kwargs):
        self.url = url
        return utils.FakeResponse({}), ParameterFakeAPI.image_list


class FakeArg(object):
    def __init__(self, arg_dict):
        self.arg_dict = arg_dict
        self.fields = arg_dict.keys()

    def __getattr__(self, name):
        if name in self.arg_dict:
            return self.arg_dict[name]
        else:
            return None


class UrlParameterTest(testtools.TestCase):

    def setUp(self):
        super(UrlParameterTest, self).setUp()
        self.api = ParameterFakeAPI({})
        self.gc = client.Client("http://fakeaddress.com")
        self.gc.images = images.ImageManager(self.api)

    def test_is_public_list(self):
        shell.do_image_list(self.gc, FakeArg({"is_public": "True"}))
        parts = parse.urlparse(self.api.url)
        qs_dict = parse.parse_qs(parts.query)
        self.assertIn('is_public', qs_dict)
        self.assertTrue(qs_dict['is_public'][0].lower() == "true")
