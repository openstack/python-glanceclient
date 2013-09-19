# Copyright 2013 OpenStack Foundation
# Copyright (C) 2013 Yahoo! Inc.
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
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import mock
import testtools

from glanceclient import client
from glanceclient import exc
from glanceclient.v1 import legacy_shell as test_shell


class LegacyShellV1Test(testtools.TestCase):
    def test_print_image_formatted(self):

        class FakeClient():
            endpoint = 'http://is.invalid'

        class FakeImage():
            id = 1
            name = 'fake_image'
            is_public = False
            protected = False
            status = 'active'
            size = '1024'
            min_ram = 512
            min_disk = 10
            properties = {'a': 'b', 'c': 'd'}
            created_at = '04.03.2013'
            owner = 'test'
            updated_at = '04.03.2013'
            deleted_at = '04.03.2013'

        test_shell.print_image_formatted(FakeClient(), FakeImage())

    def test_print_image(self):
        class FakeImage():
            id = 1
            name = 'fake_image'
            is_public = False
            protected = False
            status = 'active'
            size = '1024'
            min_ram = 512
            min_disk = 10
            properties = {'a': 'b', 'c': 'd'}
            created_at = '04.03.2013'
            owner = 'test'
            updated_at = '04.03.2013'
            deleted_at = '04.03.2013'

        gc = client.Client('1', 'http://is.invalid:8080')
        test_shell.print_image_formatted(gc, FakeImage())

    def test_get_image_fields_from_args(self):
        args = ["field=name"]
        actual = test_shell.get_image_fields_from_args(args)
        self.assertEqual({'field': 'name'}, actual)

    def test_get_image_fields_from_args_exception_raises(self):
        args = {"filed": "name"}
        self.assertRaises(
            RuntimeError, test_shell.get_image_fields_from_args, args)

    def test_get_filters_from_args(self):
        args = ["filter=name"]
        actual = test_shell.get_image_filters_from_args(args)
        self.assertEqual({'property-filter': 'name'}, actual)

    def test_get_image_filters_from_args_exception_raises(self):
        args = {"filter": "name"}
        actual = test_shell.get_image_filters_from_args(args)
        self.assertEqual(1, actual)

    def test_do_add_error(self):
        class FakeClient():
            endpoint = 'http://is.invalid'

        class args:
            fields = 'name'

        actual = test_shell.do_add(FakeClient(), args)
        self.assertEqual(1, actual)

    def test_do_add(self):
        gc = client.Client('1', 'http://is.invalid')

        class FakeImage():
            fields = ['name=test',
                      'status=active',
                      'id=test',
                      'is_public=True',
                      'protected=False',
                      'min_disk=10',
                      'container_format=ovi',
                      'status=active']
            dry_run = True

        test_args = FakeImage()
        actual = test_shell.do_add(gc, test_args)
        self.assertEqual(0, actual)

    def test_do_add_with_image_meta(self):
        gc = client.Client('1', 'http://is.invalid')

        class FakeImage():
            fields = ['name=test',
                      'status=active',
                      'is_public=True',
                      'id=test',
                      'protected=False',
                      'min_disk=10',
                      'container_format=ovi',
                      'status=active',
                      'size=256',
                      'location=test',
                      'checksum=1024',
                      'owner=test_user']
            dry_run = True

        test_args = FakeImage()
        actual = test_shell.do_add(gc, test_args)
        self.assertEqual(0, actual)

    def test_do_add_without_dry_run(self):
        gc = client.Client('1', 'http://is.invalid')

        class FakeImage():
            fields = ['name=test',
                      'status=active',
                      'is_public=True',
                      'id=test',
                      'protected=False',
                      'min_disk=10',
                      'container_format=ovi',
                      'status=active',
                      'size=256',
                      'location=test',
                      'checksum=1024',
                      'owner=test_user']
            dry_run = False
            id = 'test'
            verbose = False

        test_args = FakeImage()
        with mock.patch.object(gc.images, 'create') as mocked_create:
            mocked_create.return_value = FakeImage()
            actual = test_shell.do_add(gc, test_args)
            self.assertEqual(0, actual)

    def test_do_clear_force_true_error(self):
        class FakeImage1():
            id = 1
            name = 'fake_image'
            is_public = False
            protected = False
            status = 'active'
            size = '1024'
            min_ram = 512
            min_disk = 10
            properties = {'a': 'b', 'c': 'd'}
            created_at = '04.03.2013'
            owner = 'test'
            updated_at = '04.03.2013'
            deleted_at = '04.03.2013'
            force = True
            verbose = True

        class FakeImages():
            def __init__(self):
                self.id = 'test'
                self.name = 'test_image_name'

            def list(self):
                self.list = [FakeImage1(), FakeImage1()]
                return self.list

        class FakeClient():
            def __init__(self):
                self.images = FakeImages()

        test_args = FakeImage1()
        actual = test_shell.do_clear(FakeClient(), test_args)
        self.assertEqual(1, actual)

    def test_do_clear_force_true(self):
        class FakeImage1():
            def __init__(self):
                self.id = 1
                self.name = 'fake_image'
                self.is_public = False
                self.protected = False
                self.status = 'active'
                self.size = '1024'
                self.min_ram = 512
                self.min_disk = 10
                self.properties = {'a': 'b', 'c': 'd'}
                self.created_at = '04.03.2013'
                self.owner = 'test'
                self.updated_at = '04.03.2013'
                self.deleted_at = '04.03.2013'
                self.force = True
                self.verbose = True

            def delete(self):
                pass

        class FakeImages():
            def __init__(self):
                self.id = 'test'
                self.name = 'test_image_name'

            def list(self):
                self.list = [FakeImage1(), FakeImage1()]
                return self.list

        class FakeClient():
            def __init__(self):
                self.images = FakeImages()

        test_args = FakeImage1()
        actual = test_shell.do_clear(FakeClient(), test_args)
        self.assertEqual(0, actual)

    def test_do_update_error(self):
        class FakeClient():
            endpoint = 'http://is.invalid'

        class Image():
            fields = ['id', 'is_public', 'name']

        args = Image()
        fake_client = FakeClient()
        actual = test_shell.do_update(fake_client, args)
        self.assertEqual(1, actual)

    def test_do_update_invalid_endpoint(self):
        class Image():
            fields = ['id=test_updated', 'is_public=True', 'name=new_name']
            dry_run = False
            id = 'test'

        args = Image()
        gc = client.Client('1', 'http://is.invalid')
        self.assertRaises(
            exc.InvalidEndpoint, test_shell.do_update, gc, args)

    def test_do_update(self):
        class Image():
            fields = ['id=test_updated',
                      'status=active',
                      'is_public=True',
                      'name=new_name',
                      'protected=False']
            dry_run = True
            id = 'test'

        args = Image()
        gc = client.Client('1', 'http://is.invalid')
        actual = test_shell.do_update(gc, args)
        self.assertEqual(0, actual)

    def test_do_update_dry_run_false(self):
        class Image():
            fields = ['id=test_updated',
                      'status=active',
                      'is_public=True',
                      'name=new_name',
                      'protected=False',
                      'is_public=True']
            dry_run = False
            id = 'test'
            verbose = True
            is_public = True
            protected = False
            status = 'active'
            size = 1024
            min_ram = 512
            min_disk = 512
            properties = {'property': 'test'}
            created_at = '12.09.2013'

        args = Image()
        gc = client.Client('1', 'http://is.invalid')
        with mock.patch.object(gc.images, 'update') as mocked_update:
            mocked_update.return_value = Image()
            actual = test_shell.do_update(gc, args)
            self.assertEqual(0, actual)

    def test_do_delete(self):
        class FakeImage1():
            def __init__(self):
                self.id = 1
                self.name = 'fake_image'
                self.is_public = False
                self.protected = False
                self.status = 'active'
                self.size = '1024'
                self.min_ram = 512
                self.min_disk = 10
                self.properties = {'a': 'b', 'c': 'd'}
                self.created_at = '04.03.2013'
                self.owner = 'test'
                self.updated_at = '04.03.2013'
                self.deleted_at = '04.03.2013'
                self.force = True
                self.verbose = True

            def delete(self):
                pass

            def get(self, id):
                return FakeImage1()

        class FakeClient():
            def __init__(self):
                self.images = FakeImage1()

        actual = test_shell.do_delete(FakeClient(), FakeImage1())

    def test_show(self):
        class Image():
            fields = ['id=test_updated',
                      'status=active',
                      'is_public=True',
                      'name=new_name',
                      'protected=False']
            id = 'test_show'
            name = 'fake_image'
            is_public = False
            protected = False
            status = 'active'
            size = '1024'
            min_ram = 512
            min_disk = 10
            properties = {'a': 'b', 'c': 'd'}
            created_at = '04.03.2013'
            owner = 'test'
            updated_at = '04.03.2013'

        gc = client.Client('1', 'http://is.invalid')
        with mock.patch.object(gc.images, 'get') as mocked_get:
            mocked_get.return_value = Image()
            actual = test_shell.do_show(gc, Image())
            self.assertEqual(0, actual)

    def test_index(self):
        class Image():
            id = 'test'
            filters = {}
            limit = 18
            marker = False
            sort_key = 'test'
            kwarg = 'name'
            sort_dir = 'test'
            name = 'test'
            disk_format = 'ovi'
            container_format = 'ovi'
            size = 1024

        args = Image()
        gc = client.Client('1', 'http://is.invalid')
        with mock.patch.object(gc.images, 'list') as mocked_list:
            mocked_list.return_value = [Image(), Image()]
            actual = test_shell.do_index(gc, args)

    def test_index_return_empty(self):
        class Image():
            id = 'test'
            filters = {}
            limit = 18
            marker = False
            sort_key = 'test'
            kwarg = 'name'
            sort_dir = 'test'
            name = 'test'
            disk_format = 'ovi'
            container_format = 'ovi'
            size = 1024

        args = Image()
        gc = client.Client('1', 'http://is.invalid')
        with mock.patch.object(test_shell, '_get_images') as mocked_get:
            mocked_get.return_value = False
            actual = test_shell.do_index(gc, args)
            self.assertEqual(0, actual)

    def test_do_details(self):
        class Image():
            id = 'test'
            filters = {}
            limit = 18
            marker = False
            sort_key = 'test'
            kwarg = 'name'
            sort_dir = 'test'
            name = 'test'
            disk_format = 'ovi'
            container_format = 'ovi'
            size = 1024
            is_public = True
            protected = False
            status = 'active'
            min_ram = 512
            min_disk = 512
            properties = {}
            created_at = '12.12.12'

        args = Image()
        gc = client.Client('1', 'http://is.invalid')
        with mock.patch.object(gc.images, 'list') as mocked_list:
            mocked_list.return_value = [Image(), Image()]
            actual = test_shell.do_details(gc, args)

    def test_do_image_members(self):
        class FakeImage1():
            def __init__(self):
                self.image_id = 1
                self.name = 'fake_image'
                self.is_public = False
                self.protected = False
                self.status = 'active'
                self.size = '1024'
                self.min_ram = 512
                self.min_disk = 10
                self.properties = {'a': 'b', 'c': 'd'}
                self.created_at = '04.03.2013'
                self.owner = 'test'
                self.updated_at = '04.03.2013'
                self.deleted_at = '04.03.2013'
                self.force = True
                self.verbose = True

            def delete(self):
                pass

            def get(self, id):
                return FakeImage1()

        class FakeClient():
            def __init__(self):
                self.image_members = ImageMembers()

        class ImageMembers():
            def __init__(self):
                self.member_id = 'test'
                self.can_share = True

            def list(self, image):
                return [ImageMembers(), ImageMembers()]

        actual = test_shell.do_image_members(FakeClient(), FakeImage1())

    def test_do_member_add_error(self):
        class FakeClient():
            def __init__(self):
                self.image_members = ImageMembers()

        class FakeImage1():
            def __init__(self):
                self.member_id = 'test'
                self.fields = ["name", "id", "filter"]
                self.dry_run = True
                self.image_id = 'fake_image_id'
                self.can_share = True

            def delete(self):
                pass

            def get(self, id):
                return FakeImage1()

        class ImageMembers():
            def __init__(self):
                self.member_id = 'test'
                self.can_share = True

            def list(self, image):
                return [ImageMembers(), ImageMembers()]

        actual = test_shell.do_member_add(FakeClient(), FakeImage1())

    def test_do_member_images_empty_result(self):
        class FakeImage1():
            def __init__(self):
                self.member_id = 'test'

        gc = client.Client('1', 'http://is.invalid')
        with mock.patch.object(gc.image_members, 'list') as mocked_list:
            mocked_list.return_value = []
            actual = test_shell.do_member_images(gc, FakeImage1())
            self.assertEqual(0, actual)

    def test_do_member_replace(self):
        class FakeClient():
            def __init__(self):
                self.image_members = ImageMembers()

        class ImageMembers():
            def __init__(self):
                self.member_id = 'test'
                self.can_share = True
                self.dry_run = True
                self.image_id = "fake_image_id"

            def list(self, image):
                return [ImageMembers(), ImageMembers()]

        actual = test_shell.do_member_add(FakeClient(), ImageMembers())

    def test_do_members_replace_dry_run_true(self):
        class Fake():
            def __init__(self):
                self.dry_run = True
                self.can_share = True
                self.image_id = 'fake_id'
                self.member_id = 'test'

        gc = client.Client('1', 'http://is.invalid')
        actual = test_shell.do_members_replace(gc, Fake())

    def test_do_members_replace_dry_run_false(self):
        class Fake():
            def __init__(self):
                self.dry_run = False
                self.can_share = True
                self.image_id = 'fake_id'
                self.member_id = 'test'

        gc = client.Client('1', 'http://is.invalid')

        with mock.patch.object(gc.image_members, 'list') as mocked_list:
            mocked_list.return_value = []
            with mock.patch.object(gc.image_members, 'create'):
                actual = test_shell.do_members_replace(gc, Fake())

    def test_do_member_images(self):
        class FakeClient():
            def __init__(self):
                self.image_members = ImageMembers()

        class ImageMembers():
            def __init__(self):
                self.member_id = 'test'
                self.can_share = True
                self.dry_run = True
                self.image_id = "fake_image_id"

            def list(self, member):
                return [ImageMembers(), ImageMembers()]

        actual = test_shell.do_member_images(FakeClient(), ImageMembers())

    def test_create_pretty_table(self):
        class MyPrettyTable(test_shell.PrettyTable):
            def __init__(self):
                self.columns = []

        # Test add column
        my_pretty_table = MyPrettyTable()
        my_pretty_table.add_column(1, label='test')

        # Test make header
        test_res = my_pretty_table.make_header()
        self.assertEqual('t\n-', test_res)

        # Test make row
        result = my_pretty_table.make_row('t')
        self.assertEqual("t", result)
        result = my_pretty_table._clip_and_justify(
            data='test', width=4, just=1)
        self.assertEqual("test", result)
