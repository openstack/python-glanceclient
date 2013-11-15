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

import StringIO

import mock
import testtools

from glanceclient.common import http
from glanceclient.common import progressbar
from glanceclient.common import utils
from glanceclient.v2 import shell as test_shell
from tests import utils as test_utils


class ShellV2Test(testtools.TestCase):
    def setUp(self):
        super(ShellV2Test, self).setUp()
        self._mock_utils()
        self.gc = self._mock_glance_client()

    def _make_args(self, args):
        #NOTE(venkatesh): this conversion from a dict to an object
        # is required because the test_shell.do_xxx(gc, args) methods
        # expects the args to be attributes of an object. If passed as
        # dict directly, it throws an AttributeError.
        class Args():
            def __init__(self, entries):
                self.__dict__.update(entries)

        return Args(args)

    def _mock_glance_client(self):
        my_mocked_gc = mock.Mock()
        my_mocked_gc.schemas.return_value = 'test'
        my_mocked_gc.get.return_value = {}
        return my_mocked_gc

    def _mock_utils(self):
        utils.print_list = mock.Mock()
        utils.print_dict = mock.Mock()
        utils.save_image = mock.Mock()

    def _test_with_few_arguments(self, func, func_args, err_msg):
        with mock.patch.object(utils, 'exit') as mocked_utils_exit:
            mocked_utils_exit.return_value = '%s' % err_msg

            func(self.gc, func_args)

            mocked_utils_exit.assert_called_once_with(err_msg)

    def test_do_image_list(self):
        input = {
            'page_size': 18,
            'visibility': True,
            'member_status': 'Fake',
            'owner': 'test',
            'checksum': 'fake_checksum',
            'tag': 'fake tag'
        }
        args = self._make_args(input)
        with mock.patch.object(self.gc.images, 'list') as mocked_list:
            mocked_list.return_value = {}

            test_shell.do_image_list(self.gc, args)

            exp_img_filters = {
                'owner': 'test',
                'member_status': 'Fake',
                'visibility': True,
                'checksum': 'fake_checksum',
                'tag': 'fake tag'
            }
            mocked_list.assert_called_once_with(page_size=18,
                                                filters=exp_img_filters)
            utils.print_list.assert_called_once_with({}, ['ID', 'Name'])

    def test_do_image_show(self):
        args = self._make_args({'id': 'pass', 'page_size': 18})
        with mock.patch.object(self.gc.images, 'get') as mocked_list:
            ignore_fields = ['self', 'access', 'file', 'schema']
            expect_image = dict([(field, field) for field in ignore_fields])
            expect_image['id'] = 'pass'
            mocked_list.return_value = expect_image

            test_shell.do_image_show(self.gc, args)

            mocked_list.assert_called_once_with('pass')
            utils.print_dict.assert_called_once_with({'id': 'pass'})

    def test_do_image_create_no_user_props(self):
        args = self._make_args({'name': 'IMG-01', 'disk_format': 'vhd',
                                'container_format': 'bare'})
        with mock.patch.object(self.gc.images, 'create') as mocked_create:
            ignore_fields = ['self', 'access', 'file', 'schema']
            expect_image = dict([(field, field) for field in ignore_fields])
            expect_image['id'] = 'pass'
            expect_image['name'] = 'IMG-01'
            expect_image['disk_format'] = 'vhd'
            expect_image['container_format'] = 'bare'
            mocked_create.return_value = expect_image

            test_shell.do_image_create(self.gc, args)

            mocked_create.assert_called_once_with(name='IMG-01',
                                                  disk_format='vhd',
                                                  container_format='bare')
            utils.print_dict.assert_called_once_with({
                'id': 'pass', 'name': 'IMG-01', 'disk_format': 'vhd',
                'container_format': 'bare'})

    def test_do_image_create_with_user_props(self):
        args = self._make_args({'name': 'IMG-01',
                                'property': ['myprop=myval']})
        with mock.patch.object(self.gc.images, 'create') as mocked_create:
            ignore_fields = ['self', 'access', 'file', 'schema']
            expect_image = dict([(field, field) for field in ignore_fields])
            expect_image['id'] = 'pass'
            expect_image['name'] = 'IMG-01'
            expect_image['myprop'] = 'myval'
            mocked_create.return_value = expect_image

            test_shell.do_image_create(self.gc, args)

            mocked_create.assert_called_once_with(name='IMG-01',
                                                  myprop='myval')
            utils.print_dict.assert_called_once_with({
                'id': 'pass', 'name': 'IMG-01', 'myprop': 'myval'})

    def test_do_image_update_no_user_props(self):
        args = self._make_args({'id': 'pass', 'name': 'IMG-01',
                                'disk_format': 'vhd',
                                'container_format': 'bare'})
        with mock.patch.object(self.gc.images, 'update') as mocked_update:
            ignore_fields = ['self', 'access', 'file', 'schema']
            expect_image = dict([(field, field) for field in ignore_fields])
            expect_image['id'] = 'pass'
            expect_image['name'] = 'IMG-01'
            expect_image['disk_format'] = 'vhd'
            expect_image['container_format'] = 'bare'
            mocked_update.return_value = expect_image

            test_shell.do_image_update(self.gc, args)

            mocked_update.assert_called_once_with('pass',
                                                  None,
                                                  name='IMG-01',
                                                  disk_format='vhd',
                                                  container_format='bare')
            utils.print_dict.assert_called_once_with({
                'id': 'pass', 'name': 'IMG-01', 'disk_format': 'vhd',
                'container_format': 'bare'})

    def test_do_image_update_with_user_props(self):
        args = self._make_args({'id': 'pass', 'name': 'IMG-01',
                                'property': ['myprop=myval']})
        with mock.patch.object(self.gc.images, 'update') as mocked_update:
            ignore_fields = ['self', 'access', 'file', 'schema']
            expect_image = dict([(field, field) for field in ignore_fields])
            expect_image['id'] = 'pass'
            expect_image['name'] = 'IMG-01'
            expect_image['myprop'] = 'myval'
            mocked_update.return_value = expect_image

            test_shell.do_image_update(self.gc, args)

            mocked_update.assert_called_once_with('pass',
                                                  None,
                                                  name='IMG-01',
                                                  myprop='myval')
            utils.print_dict.assert_called_once_with({
                'id': 'pass', 'name': 'IMG-01', 'myprop': 'myval'})

    def test_do_image_update_with_remove_props(self):
        args = self._make_args({'id': 'pass', 'name': 'IMG-01',
                                'disk_format': 'vhd',
                                'remove-property': ['container_format']})
        with mock.patch.object(self.gc.images, 'update') as mocked_update:
            ignore_fields = ['self', 'access', 'file', 'schema']
            expect_image = dict([(field, field) for field in ignore_fields])
            expect_image['id'] = 'pass'
            expect_image['name'] = 'IMG-01'
            expect_image['disk_format'] = 'vhd'

            mocked_update.return_value = expect_image

            test_shell.do_image_update(self.gc, args)

            mocked_update.assert_called_once_with('pass',
                                                  ['container_format'],
                                                  name='IMG-01',
                                                  disk_format='vhd')
            utils.print_dict.assert_called_once_with({
                'id': 'pass', 'name': 'IMG-01', 'disk_format': 'vhd'})

    def test_do_explain(self):
        input = {
            'page_size': 18,
            'id': 'pass',
            'schemas': 'test',
            'model': 'test',
        }
        args = self._make_args(input)
        with mock.patch.object(utils, 'print_list'):
            test_shell.do_explain(self.gc, args)

            self.gc.schemas.get.assert_called_once_with('test')

    def test_image_upload(self):
        args = self._make_args({'id': 'IMG-01', 'file': 'test'})

        with mock.patch.object(self.gc.images, 'upload') as mocked_upload:
            utils.get_data_file = mock.Mock(return_value='testfile')
            mocked_upload.return_value = None
            test_shell.do_image_upload(self.gc, args)
            mocked_upload.assert_called_once_with('IMG-01', 'testfile')

    def test_image_download(self):
        args = self._make_args(
            {'id': 'pass', 'file': 'test', 'progress': False})

        with mock.patch.object(self.gc.images, 'data') as mocked_data:
            resp = test_utils.FakeResponse({}, StringIO.StringIO('CCC'))
            ret = mocked_data.return_value = http.ResponseBodyIterator(resp)
            test_shell.do_image_download(self.gc, args)

            mocked_data.assert_called_once_with('pass')
            utils.save_image.assert_called_once_with(ret, 'test')

    def test_image_download_with_progressbar(self):
        args = self._make_args(
            {'id': 'pass', 'file': 'test', 'progress': True})

        with mock.patch.object(self.gc.images, 'data') as mocked_data:
            resp = test_utils.FakeResponse({}, StringIO.StringIO('CCC'))
            mocked_data.return_value = http.ResponseBodyIterator(resp)
            test_shell.do_image_download(self.gc, args)

            mocked_data.assert_called_once_with('pass')
            utils.save_image.assert_called_once_with(mock.ANY, 'test')
            self.assertIsInstance(
                utils.save_image.call_args[0][0],
                progressbar.VerboseIteratorWrapper
            )

    def test_do_image_delete(self):
        args = self._make_args({'id': 'pass', 'file': 'test'})
        with mock.patch.object(self.gc.images, 'delete') as mocked_delete:
            mocked_delete.return_value = 0

            test_shell.do_image_delete(self.gc, args)

            mocked_delete.assert_called_once_with('pass')

    def test_do_member_list(self):
        args = self._make_args({'image_id': 'IMG-01'})
        with mock.patch.object(self.gc.image_members, 'list') as mocked_list:
            mocked_list.return_value = {}

            test_shell.do_member_list(self.gc, args)

            mocked_list.assert_called_once_with('IMG-01')
            columns = ['Image ID', 'Member ID', 'Status']
            utils.print_list.assert_called_once_with({}, columns)

    def test_do_member_create(self):
        args = self._make_args({'image_id': 'IMG-01', 'member_id': 'MEM-01'})
        with mock.patch.object(self.gc.image_members, 'create') as mock_create:
            mock_create.return_value = {}

            test_shell.do_member_create(self.gc, args)

            mock_create.assert_called_once_with('IMG-01', 'MEM-01')
            columns = ['Image ID', 'Member ID', 'Status']
            utils.print_list.assert_called_once_with([{}], columns)

    def test_do_member_create_with_few_arguments(self):
        args = self._make_args({'image_id': None, 'member_id': 'MEM-01'})
        msg = 'Unable to create member. Specify image_id and member_id'

        self._test_with_few_arguments(func=test_shell.do_member_create,
                                      func_args=args,
                                      err_msg=msg)

    def test_do_member_update(self):
        input = {
            'image_id': 'IMG-01',
            'member_id': 'MEM-01',
            'member_status': 'status',
        }
        args = self._make_args(input)
        with mock.patch.object(self.gc.image_members, 'update') as mock_update:
            mock_update.return_value = {}

            test_shell.do_member_update(self.gc, args)

            mock_update.assert_called_once_with('IMG-01', 'MEM-01', 'status')
            columns = ['Image ID', 'Member ID', 'Status']
            utils.print_list.assert_called_once_with([{}], columns)

    def test_do_member_update_with_few_arguments(self):
        input = {
            'image_id': 'IMG-01',
            'member_id': 'MEM-01',
            'member_status': None,
        }
        args = self._make_args(input)
        msg = 'Unable to update member. Specify image_id, member_id' \
              ' and member_status'

        self._test_with_few_arguments(func=test_shell.do_member_update,
                                      func_args=args,
                                      err_msg=msg)

    def test_do_member_delete(self):
        args = self._make_args({'image_id': 'IMG-01', 'member_id': 'MEM-01'})
        with mock.patch.object(self.gc.image_members, 'delete') as mock_delete:
            test_shell.do_member_delete(self.gc, args)

            mock_delete.assert_called_once_with('IMG-01', 'MEM-01')

    def test_do_member_delete_with_few_arguments(self):
        args = self._make_args({'image_id': None, 'member_id': 'MEM-01'})
        msg = 'Unable to delete member. Specify image_id and member_id'

        self._test_with_few_arguments(func=test_shell.do_member_delete,
                                      func_args=args,
                                      err_msg=msg)

    def test_image_tag_update(self):
        args = self._make_args({'image_id': 'IMG-01', 'tag_value': 'tag01'})
        with mock.patch.object(self.gc.image_tags, 'update') as mocked_update:
            self.gc.images.get = mock.Mock(return_value={})
            mocked_update.return_value = None

            test_shell.do_image_tag_update(self.gc, args)

            mocked_update.assert_called_once_with('IMG-01', 'tag01')

    def test_image_tag_update_with_few_arguments(self):
        args = self._make_args({'image_id': None, 'tag_value': 'tag01'})
        msg = 'Unable to update tag. Specify image_id and tag_value'

        self._test_with_few_arguments(func=test_shell.do_image_tag_update,
                                      func_args=args,
                                      err_msg=msg)

    def test_image_tag_delete(self):
        args = self._make_args({'image_id': 'IMG-01', 'tag_value': 'tag01'})
        with mock.patch.object(self.gc.image_tags, 'delete') as mocked_delete:
            mocked_delete.return_value = None

            test_shell.do_image_tag_delete(self.gc, args)

            mocked_delete.assert_called_once_with('IMG-01', 'tag01')

    def test_image_tag_delete_with_few_arguments(self):
        args = self._make_args({'image_id': 'IMG-01', 'tag_value': None})
        msg = 'Unable to delete tag. Specify image_id and tag_value'

        self._test_with_few_arguments(func=test_shell.do_image_tag_delete,
                                      func_args=args,
                                      err_msg=msg)
