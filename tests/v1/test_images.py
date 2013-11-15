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
import json
import StringIO
import sys
import testtools
import urlparse

from glanceclient.v1 import client
from glanceclient.v1 import images
from glanceclient.v1 import legacy_shell
from glanceclient.v1 import shell
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
    '/v1/images/detail?is_public=None&limit=20': {
        'GET': (
            {},
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
    '/v1/images/detail?marker=a&limit=1': {
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
    '/v1/images/detail?property-ping=pong&limit=20':
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
    '/v1/images/detail?sort_dir=desc&limit=20': {
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
    '/v1/images/detail?sort_key=name&limit=20': {
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
                'x-image-meta-name': "ni\xc3\xb1o"
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


class ImageManagerTest(testtools.TestCase):

    def setUp(self):
        super(ImageManagerTest, self).setUp()
        self.api = utils.FakeAPI(fixtures)
        self.mgr = images.ImageManager(self.api)

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
        results = list(self.mgr.list(page_size=2, limit=1))
        expect = [('GET', '/v1/images/detail?limit=2', {}, None)]
        self.assertEqual(1, len(results))
        self.assertEqual(self.api.calls, expect)

    def test_list_with_limit_greater_than_page_size(self):
        images = list(self.mgr.list(page_size=1, limit=2))
        expect = [
            ('GET', '/v1/images/detail?limit=1', {}, None),
            ('GET', '/v1/images/detail?marker=a&limit=1', {}, None),
        ]
        self.assertEqual(len(images), 2)
        self.assertEqual(images[0].id, 'a')
        self.assertEqual(images[1].id, 'b')
        self.assertEqual(self.api.calls, expect)

    def test_list_with_marker(self):
        list(self.mgr.list(marker='a'))
        url = '/v1/images/detail?marker=a&limit=20'
        expect = [('GET', url, {}, None)]
        self.assertEqual(self.api.calls, expect)

    def test_list_with_filter(self):
        list(self.mgr.list(filters={'name': "foo"}))
        url = '/v1/images/detail?limit=20&name=foo'
        expect = [('GET', url, {}, None)]
        self.assertEqual(self.api.calls, expect)

    def test_list_with_property_filters(self):
        list(self.mgr.list(filters={'properties': {'ping': 'pong'}}))
        url = '/v1/images/detail?property-ping=pong&limit=20'
        expect = [('GET', url, {}, None)]
        self.assertEqual(self.api.calls, expect)

    def test_list_with_sort_dir(self):
        list(self.mgr.list(sort_dir='desc'))
        url = '/v1/images/detail?sort_dir=desc&limit=20'
        expect = [('GET', url, {}, None)]
        self.assertEqual(self.api.calls, expect)

    def test_list_with_sort_key(self):
        list(self.mgr.list(sort_key='name'))
        url = '/v1/images/detail?sort_key=name&limit=20'
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
        self.assertEqual(image.properties, {u'arch': u'x86_64'})

    def test_get_int(self):
        image = self.mgr.get(1)
        expect = [('HEAD', '/v1/images/1', {}, None)]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(image.id, '1')
        self.assertEqual(image.name, 'image-1')
        self.assertEqual(image.is_public, False)
        self.assertEqual(image.protected, False)
        self.assertEqual(image.deleted, False)
        self.assertEqual(image.properties, {u'arch': u'x86_64'})

    def test_get_encoding(self):
        image = self.mgr.get('3')
        expect = [('HEAD', '/v1/images/3', {}, None)]
        self.assertEqual(image.name, u"ni\xf1o")

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
        except IOError as e:
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

    def test_image_meta_from_headers_encoding(self):
        fields = {"x-image-meta-name": "ni\xc3\xb1o"}
        headers = self.mgr._image_meta_from_headers(fields)
        self.assertEqual(headers["name"], u"ni\xf1o")

    def test_image_list_with_owner(self):
        images = self.mgr.list(owner='A', page_size=20)
        image_list = list(images)
        self.assertEqual(image_list[0].owner, 'A')
        self.assertEqual(image_list[0].id, 'a')
        self.assertEqual(len(image_list), 1)

    def test_image_list_with_notfound_owner(self):
        images = self.mgr.list(owner='X', page_size=20)
        self.assertEqual(len(list(images)), 0)

    def test_image_list_with_empty_string_owner(self):
        images = self.mgr.list(owner='', page_size=20)
        image_list = list(images)
        self.assertRaises(AttributeError, lambda: image_list[0].owner)
        self.assertEqual(image_list[0].id, 'c')
        self.assertEqual(len(image_list), 1)

    def test_image_list_with_unspecified_owner(self):
        images = self.mgr.list(owner=None, page_size=5)
        image_list = list(images)
        self.assertEqual(image_list[0].owner, 'A')
        self.assertEqual(image_list[0].id, 'a')
        self.assertEqual(image_list[1].owner, 'A')
        self.assertEqual(image_list[1].id, 'b')
        self.assertEqual(image_list[2].owner, 'B')
        self.assertEqual(image_list[2].id, 'b2')
        self.assertRaises(AttributeError, lambda: image_list[3].owner)
        self.assertEqual(image_list[3].id, 'c')
        self.assertEqual(len(image_list), 4)

    def test_image_list_with_owner_and_limit(self):
        images = self.mgr.list(owner='B', page_size=5, limit=1)
        image_list = list(images)
        self.assertEqual(image_list[0].owner, 'B')
        self.assertEqual(image_list[0].id, 'b')
        self.assertEqual(len(image_list), 1)

    def test_image_list_all_tenants(self):
        images = self.mgr.list(is_public=None, page_size=5)
        image_list = list(images)
        self.assertEqual(image_list[0].owner, 'A')
        self.assertEqual(image_list[0].id, 'a')
        self.assertEqual(image_list[1].owner, 'B')
        self.assertEqual(image_list[1].id, 'b')
        self.assertEqual(image_list[2].owner, 'B')
        self.assertEqual(image_list[2].id, 'b2')
        self.assertRaises(AttributeError, lambda: image_list[3].owner)
        self.assertEqual(image_list[3].id, 'c')
        self.assertEqual(len(image_list), 4)


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
        except IOError as e:
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

    def json_request(self, method, url, **kwargs):
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
        parts = urlparse.urlparse(self.api.url)
        qs_dict = urlparse.parse_qs(parts.query)
        self.assertTrue('is_public' in qs_dict)
        self.assertTrue(qs_dict['is_public'][0].lower() == "true")

    def test_copy_from_used(self):
        class LegacyFakeArg(object):
            def __init__(self, fields):
                self.fields = fields
                self.dry_run = False
                self.verbose = False

        def images_create(**kwargs):
            class FakeImage():
                id = "ThisiSanID"
            self.assertNotEqual(kwargs['data'], sys.stdin)
            return FakeImage()

        self.gc.images.create = images_create
        args = LegacyFakeArg(["copy_from=http://somehost.com/notreal.qcow"])
        legacy_shell.do_add(self.gc, args)
