
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

    def test_create(self):
        image = self.mgr.create(name='image-1')
        expect = [('POST', '/v1/images', {}, {'image': {'name': 'image-1'}})]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(image.id, '1')
        self.assertEqual(image.name, 'image-1')

    def test_update(self):
        image = self.mgr.update('1', name='image-2')
        expect_hdrs = {'x-image-meta-name': 'image-2'}
        expect = [('PUT', '/v1/images/1', expect_hdrs, None)]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(image.id, '1')
        self.assertEqual(image.name, 'image-2')
