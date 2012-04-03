
import unittest

from tests.v1 import utils

import glanceclient.v1.images


class ImageManagerTest(unittest.TestCase):

    def setUp(self):
        self.api = utils.FakeAPI()
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

    def test_get(self):
        image = self.mgr.get('1')
        expect = [('HEAD', '/v1/images/1', {}, None)]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(image.id, '1')
        self.assertEqual(image.name, 'image-1')

    def test_delete(self):
        self.mgr.delete('1')
        expect = [('DELETE', '/v1/images/1', {}, None)]
        self.assertEqual(self.api.calls, expect)

    def test_create_no_data(self):
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

    def test_update(self):
        image = self.mgr.update('1', name='image-2')
        expect_hdrs = {'x-image-meta-name': 'image-2'}
        expect = [('PUT', '/v1/images/1', expect_hdrs, None)]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(image.id, '1')
        self.assertEqual(image.name, 'image-2')


class ImageTest(unittest.TestCase):
    def setUp(self):
        self.api = utils.FakeAPI()
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
