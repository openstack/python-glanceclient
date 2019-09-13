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
import argparse
from copy import deepcopy
import json
import mock
import os
import six
import sys
import tempfile
import testtools

from glanceclient.common import utils
from glanceclient import exc
from glanceclient import shell

# NOTE(geguileo): This is very nasty, but I can't find a better way to set
# command line arguments in glanceclient.v2.shell.do_image_create that are
# set by decorator utils.schema_args while preserving the spirits of the test

# Backup original decorator
original_schema_args = utils.schema_args


# Set our own decorator that calls the original but with simulated schema
def schema_args(schema_getter, omit=None):
    global original_schema_args
    # We only add the 2 arguments that are required by image-create
    my_schema_getter = lambda: {
        'properties': {
            'container_format': {
                'enum': [None, 'ami', 'ari', 'aki', 'bare', 'ovf', 'ova',
                         'docker'],
                'type': 'string',
                'description': 'Format of the container'},
            'disk_format': {
                'enum': [None, 'ami', 'ari', 'aki', 'vhd', 'vhdx', 'vmdk',
                         'raw', 'qcow2', 'vdi', 'iso', 'ploop'],
                'type': 'string',
                'description': 'Format of the disk'},
            'location': {'type': 'string'},
            'locations': {'type': 'string'},
            'copy_from': {'type': 'string'}}}
    return original_schema_args(my_schema_getter, omit)
utils.schema_args = schema_args

from glanceclient.v2 import shell as test_shell  # noqa

# Return original decorator.
utils.schema_args = original_schema_args


class ShellV2Test(testtools.TestCase):
    def setUp(self):
        super(ShellV2Test, self).setUp()
        self._mock_utils()
        self.gc = self._mock_glance_client()
        self.shell = shell.OpenStackImagesShell()
        os.environ = {
            'OS_USERNAME': 'username',
            'OS_PASSWORD': 'password',
            'OS_TENANT_ID': 'tenant_id',
            'OS_TOKEN_ID': 'test',
            'OS_AUTH_URL': 'http://127.0.0.1:5000/v2.0/',
            'OS_AUTH_TOKEN': 'pass',
            'OS_IMAGE_API_VERSION': '1',
            'OS_REGION_NAME': 'test',
            'OS_IMAGE_URL': 'http://is.invalid'}
        self.shell = shell.OpenStackImagesShell()
        self.patched = mock.patch('glanceclient.common.utils.get_data_file',
                                  autospec=True, return_value=None)
        self.mock_get_data_file = self.patched.start()

    def tearDown(self):
        super(ShellV2Test, self).tearDown()
        self.patched.stop()

    def _make_args(self, args):
        # NOTE(venkatesh): this conversion from a dict to an object
        # is required because the test_shell.do_xxx(gc, args) methods
        # expects the args to be attributes of an object. If passed as
        # dict directly, it throws an AttributeError.
        class Args(object):
            def __init__(self, entries):
                self.store = None
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

    def assert_exits_with_msg(self, func, func_args, err_msg=None):
        with mock.patch.object(utils, 'exit') as mocked_utils_exit:
            mocked_utils_exit.return_value = '%s' % err_msg

            func(self.gc, func_args)
            if err_msg:
                mocked_utils_exit.assert_called_once_with(err_msg)
            else:
                mocked_utils_exit.assert_called_once_with()

    def _run_command(self, cmd):
        self.shell.main(cmd.split())

    stores_info_response = {
        "stores": [
            {
                "default": "true",
                "id": "ceph1",
                "description": "RBD backend for glance."
            },
            {
                "id": "file2",
                "description": "Filesystem backend for glance."
            },
            {
                "id": "file1",
                "description": "Filesystem backend for gkance."
            },
            {
                "id": "ceph2",
                "description": "RBD backend for glance."
            }
        ]
    }

    def test_do_stores_info(self):
        args = []
        with mock.patch.object(self.gc.images,
                               'get_stores_info') as mocked_list:
            mocked_list.return_value = self.stores_info_response

            test_shell.do_stores_info(self.gc, args)

            mocked_list.assert_called_once_with()
            utils.print_dict.assert_called_once_with(self.stores_info_response)

    @mock.patch('glanceclient.common.utils.exit')
    @mock.patch('sys.stdin', autospec=True)
    def test_neg_stores_info(
            self, mock_stdin, mock_utils_exit):
        expected_msg = ('Multi Backend support is not enabled')
        args = []
        mock_utils_exit.side_effect = self._mock_utils_exit
        with mock.patch.object(self.gc.images,
                               'get_stores_info') as mocked_info:
            mocked_info.side_effect = exc.HTTPNotFound
            try:
                test_shell.do_stores_info(self.gc, args)
                self.fail("utils.exit should have been called")
            except SystemExit:
                pass
        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('sys.stderr')
    def test_image_create_missing_disk_format(self, __):
        e = self.assertRaises(exc.CommandError, self._run_command,
                              '--os-image-api-version 2 image-create ' +
                              '--file fake_src --container-format bare')
        self.assertEqual('error: Must provide --disk-format when using '
                         '--file.', e.message)

    @mock.patch('sys.stderr')
    def test_image_create_missing_container_format(self, __):
        e = self.assertRaises(exc.CommandError, self._run_command,
                              '--os-image-api-version 2 image-create ' +
                              '--file fake_src --disk-format qcow2')
        self.assertEqual('error: Must provide --container-format when '
                         'using --file.', e.message)

    @mock.patch('sys.stderr')
    def test_image_create_missing_container_format_stdin_data(self, __):
        # Fake that get_data_file method returns data
        self.mock_get_data_file.return_value = six.StringIO()
        e = self.assertRaises(exc.CommandError, self._run_command,
                              '--os-image-api-version 2 image-create'
                              ' --disk-format qcow2')
        self.assertEqual('error: Must provide --container-format when '
                         'using stdin.', e.message)

    @mock.patch('sys.stderr')
    def test_image_create_missing_disk_format_stdin_data(self, __):
        # Fake that get_data_file method returns data
        self.mock_get_data_file.return_value = six.StringIO()
        e = self.assertRaises(exc.CommandError, self._run_command,
                              '--os-image-api-version 2 image-create'
                              ' --container-format bare')
        self.assertEqual('error: Must provide --disk-format when using stdin.',
                         e.message)

    @mock.patch('sys.stderr')
    def test_create_via_import_glance_direct_missing_disk_format(self, __):
        e = self.assertRaises(exc.CommandError, self._run_command,
                              '--os-image-api-version 2 '
                              'image-create-via-import '
                              '--file fake_src --container-format bare')
        self.assertEqual('error: Must provide --disk-format when using '
                         '--file.', e.message)

    @mock.patch('sys.stderr')
    def test_create_via_import_glance_direct_missing_container_format(
            self, __):
        e = self.assertRaises(exc.CommandError, self._run_command,
                              '--os-image-api-version 2 '
                              'image-create-via-import '
                              '--file fake_src --disk-format qcow2')
        self.assertEqual('error: Must provide --container-format when '
                         'using --file.', e.message)

    @mock.patch('sys.stderr')
    def test_create_via_import_web_download_missing_disk_format(self, __):
        e = self.assertRaises(exc.CommandError, self._run_command,
                              '--os-image-api-version 2 '
                              'image-create-via-import ' +
                              '--import-method web-download ' +
                              '--uri fake_uri --container-format bare')
        self.assertEqual('error: Must provide --disk-format when using '
                         '--uri.', e.message)

    @mock.patch('sys.stderr')
    def test_create_via_import_web_download_missing_container_format(
            self, __):
        e = self.assertRaises(exc.CommandError, self._run_command,
                              '--os-image-api-version 2 '
                              'image-create-via-import '
                              '--import-method web-download '
                              '--uri fake_uri --disk-format qcow2')
        self.assertEqual('error: Must provide --container-format when '
                         'using --uri.', e.message)

    def test_do_image_list(self):
        input = {
            'limit': None,
            'page_size': 18,
            'visibility': True,
            'member_status': 'Fake',
            'owner': 'test',
            'checksum': 'fake_checksum',
            'tag': 'fake tag',
            'properties': [],
            'sort_key': ['name', 'id'],
            'sort_dir': ['desc', 'asc'],
            'sort': None,
            'verbose': False,
            'include_stores': False,
            'os_hash_value': None,
            'os_hidden': False
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
                'tag': 'fake tag',
                'os_hidden': False
            }
            mocked_list.assert_called_once_with(page_size=18,
                                                sort_key=['name', 'id'],
                                                sort_dir=['desc', 'asc'],
                                                filters=exp_img_filters)
            utils.print_list.assert_called_once_with({}, ['ID', 'Name'])

    def test_do_image_list_verbose(self):
        input = {
            'limit': None,
            'page_size': 18,
            'visibility': True,
            'member_status': 'Fake',
            'owner': 'test',
            'checksum': 'fake_checksum',
            'tag': 'fake tag',
            'properties': [],
            'sort_key': ['name', 'id'],
            'sort_dir': ['desc', 'asc'],
            'sort': None,
            'verbose': True,
            'include_stores': False,
            'os_hash_value': None,
            'os_hidden': False
        }
        args = self._make_args(input)
        with mock.patch.object(self.gc.images, 'list') as mocked_list:
            mocked_list.return_value = {}

            test_shell.do_image_list(self.gc, args)
            utils.print_list.assert_called_once_with(
                {}, ['ID', 'Name', 'Disk_format', 'Container_format',
                     'Size', 'Status', 'Owner'])

    def test_do_image_list_with_include_stores_true(self):
        input = {
            'limit': None,
            'page_size': 18,
            'visibility': True,
            'member_status': 'Fake',
            'owner': 'test',
            'checksum': 'fake_checksum',
            'tag': 'fake tag',
            'properties': [],
            'sort_key': ['name', 'id'],
            'sort_dir': ['desc', 'asc'],
            'sort': None,
            'verbose': False,
            'include_stores': True,
            'os_hash_value': None,
            'os_hidden': False
        }
        args = self._make_args(input)
        with mock.patch.object(self.gc.images, 'list') as mocked_list:
            mocked_list.return_value = {}

            test_shell.do_image_list(self.gc, args)
            utils.print_list.assert_called_once_with(
                {}, ['ID', 'Name', 'Stores'])

    def test_do_image_list_verbose_with_include_stores_true(self):
        input = {
            'limit': None,
            'page_size': 18,
            'visibility': True,
            'member_status': 'Fake',
            'owner': 'test',
            'checksum': 'fake_checksum',
            'tag': 'fake tag',
            'properties': [],
            'sort_key': ['name', 'id'],
            'sort_dir': ['desc', 'asc'],
            'sort': None,
            'verbose': True,
            'include_stores': True,
            'os_hash_value': None,
            'os_hidden': False
        }
        args = self._make_args(input)
        with mock.patch.object(self.gc.images, 'list') as mocked_list:
            mocked_list.return_value = {}

            test_shell.do_image_list(self.gc, args)
            utils.print_list.assert_called_once_with(
                {}, ['ID', 'Name', 'Disk_format', 'Container_format',
                     'Size', 'Status', 'Owner', 'Stores'])

    def test_do_image_list_with_hidden_true(self):
        input = {
            'limit': None,
            'page_size': 18,
            'visibility': True,
            'member_status': 'Fake',
            'owner': 'test',
            'checksum': 'fake_checksum',
            'tag': 'fake tag',
            'properties': [],
            'sort_key': ['name', 'id'],
            'sort_dir': ['desc', 'asc'],
            'sort': None,
            'verbose': False,
            'include_stores': False,
            'os_hash_value': None,
            'os_hidden': True
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
                'tag': 'fake tag',
                'os_hidden': True
            }
            mocked_list.assert_called_once_with(page_size=18,
                                                sort_key=['name', 'id'],
                                                sort_dir=['desc', 'asc'],
                                                filters=exp_img_filters)
            utils.print_list.assert_called_once_with({}, ['ID', 'Name'])

    def test_do_image_list_with_single_sort_key(self):
        input = {
            'limit': None,
            'page_size': 18,
            'visibility': True,
            'member_status': 'Fake',
            'owner': 'test',
            'checksum': 'fake_checksum',
            'tag': 'fake tag',
            'properties': [],
            'sort_key': ['name'],
            'sort_dir': ['desc'],
            'sort': None,
            'verbose': False,
            'include_stores': False,
            'os_hash_value': None,
            'os_hidden': False
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
                'tag': 'fake tag',
                'os_hidden': False
            }
            mocked_list.assert_called_once_with(page_size=18,
                                                sort_key=['name'],
                                                sort_dir=['desc'],
                                                filters=exp_img_filters)
            utils.print_list.assert_called_once_with({}, ['ID', 'Name'])

    def test_do_image_list_new_sorting_syntax(self):
        input = {
            'limit': None,
            'page_size': 18,
            'visibility': True,
            'member_status': 'Fake',
            'owner': 'test',
            'checksum': 'fake_checksum',
            'tag': 'fake tag',
            'properties': [],
            'sort': 'name:desc,size:asc',
            'sort_key': [],
            'sort_dir': [],
            'verbose': False,
            'include_stores': False,
            'os_hash_value': None,
            'os_hidden': False
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
                'tag': 'fake tag',
                'os_hidden': False
            }
            mocked_list.assert_called_once_with(
                page_size=18,
                sort='name:desc,size:asc',
                filters=exp_img_filters)
            utils.print_list.assert_called_once_with({}, ['ID', 'Name'])

    def test_do_image_list_with_property_filter(self):
        input = {
            'limit': None,
            'page_size': 1,
            'visibility': True,
            'member_status': 'Fake',
            'owner': 'test',
            'checksum': 'fake_checksum',
            'tag': 'fake tag',
            'properties': ['os_distro=NixOS', 'architecture=x86_64'],
            'sort_key': ['name'],
            'sort_dir': ['desc'],
            'sort': None,
            'verbose': False,
            'include_stores': False,
            'os_hash_value': None,
            'os_hidden': False
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
                'tag': 'fake tag',
                'os_distro': 'NixOS',
                'architecture': 'x86_64',
                'os_hidden': False
            }

            mocked_list.assert_called_once_with(page_size=1,
                                                sort_key=['name'],
                                                sort_dir=['desc'],
                                                filters=exp_img_filters)
            utils.print_list.assert_called_once_with({}, ['ID', 'Name'])

    def test_do_image_show_human_readable(self):
        args = self._make_args({'id': 'pass', 'page_size': 18,
                                'human_readable': True,
                                'max_column_width': 120})
        with mock.patch.object(self.gc.images, 'get') as mocked_list:
            ignore_fields = ['self', 'access', 'file', 'schema']
            expect_image = dict([(field, field) for field in ignore_fields])
            expect_image['id'] = 'pass'
            expect_image['size'] = 1024
            mocked_list.return_value = expect_image

            test_shell.do_image_show(self.gc, args)

            mocked_list.assert_called_once_with('pass')
            utils.print_dict.assert_called_once_with({'id': 'pass',
                                                      'size': '1kB'},
                                                     max_column_width=120)

    def test_do_image_show(self):
        args = self._make_args({'id': 'pass', 'page_size': 18,
                                'human_readable': False,
                                'max_column_width': 120})
        with mock.patch.object(self.gc.images, 'get') as mocked_list:
            ignore_fields = ['self', 'access', 'file', 'schema']
            expect_image = dict([(field, field) for field in ignore_fields])
            expect_image['id'] = 'pass'
            expect_image['size'] = 1024
            mocked_list.return_value = expect_image

            test_shell.do_image_show(self.gc, args)

            mocked_list.assert_called_once_with('pass')
            utils.print_dict.assert_called_once_with({'id': 'pass',
                                                      'size': 1024},
                                                     max_column_width=120)

    @mock.patch('sys.stdin', autospec=True)
    def test_do_image_create_no_user_props(self, mock_stdin):
        args = self._make_args({'name': 'IMG-01', 'disk_format': 'vhd',
                                'container_format': 'bare',
                                'file': None})
        with mock.patch.object(self.gc.images, 'create') as mocked_create:
            ignore_fields = ['self', 'access', 'file', 'schema']
            expect_image = dict([(field, field) for field in ignore_fields])
            expect_image['id'] = 'pass'
            expect_image['name'] = 'IMG-01'
            expect_image['disk_format'] = 'vhd'
            expect_image['container_format'] = 'bare'
            mocked_create.return_value = expect_image

            # Ensure that the test stdin is not considered
            # to be supplying image data
            mock_stdin.isatty = lambda: True
            test_shell.do_image_create(self.gc, args)

            mocked_create.assert_called_once_with(name='IMG-01',
                                                  disk_format='vhd',
                                                  container_format='bare')
            utils.print_dict.assert_called_once_with({
                'id': 'pass', 'name': 'IMG-01', 'disk_format': 'vhd',
                'container_format': 'bare'})

    @mock.patch('sys.stdin', autospec=True)
    def test_do_image_create_for_none_multi_hash(self, mock_stdin):
        args = self._make_args({'name': 'IMG-01', 'disk_format': 'vhd',
                                'container_format': 'bare',
                                'file': None})
        with mock.patch.object(self.gc.images, 'create') as mocked_create:
            ignore_fields = ['self', 'access', 'file', 'schema']
            expect_image = dict([(field, field) for field in ignore_fields])
            expect_image['id'] = 'pass'
            expect_image['name'] = 'IMG-01'
            expect_image['disk_format'] = 'vhd'
            expect_image['container_format'] = 'bare'
            expect_image['os_hash_algo'] = None
            expect_image['os_hash_value'] = None
            mocked_create.return_value = expect_image

            # Ensure that the test stdin is not considered
            # to be supplying image data
            mock_stdin.isatty = lambda: True
            test_shell.do_image_create(self.gc, args)

            mocked_create.assert_called_once_with(name='IMG-01',
                                                  disk_format='vhd',
                                                  container_format='bare')
            utils.print_dict.assert_called_once_with({
                'id': 'pass', 'name': 'IMG-01', 'disk_format': 'vhd',
                'container_format': 'bare', 'os_hash_algo': None,
                'os_hash_value': None})

    def test_do_image_create_with_multihash(self):
        self.mock_get_data_file.return_value = six.StringIO()
        try:
            with open(tempfile.mktemp(), 'w+') as f:
                f.write('Some data here')
                f.flush()
                f.seek(0)
                file_name = f.name
            temp_args = {'name': 'IMG-01',
                         'disk_format': 'vhd',
                         'container_format': 'bare',
                         'file': file_name,
                         'progress': False}
            args = self._make_args(temp_args)
            with mock.patch.object(self.gc.images, 'create') as mocked_create:
                with mock.patch.object(self.gc.images, 'get') as mocked_get:

                    ignore_fields = ['self', 'access', 'schema']
                    expect_image = dict([(field, field) for field in
                                         ignore_fields])
                    expect_image['id'] = 'pass'
                    expect_image['name'] = 'IMG-01'
                    expect_image['disk_format'] = 'vhd'
                    expect_image['container_format'] = 'bare'
                    expect_image['checksum'] = 'fake-checksum'
                    expect_image['os_hash_algo'] = 'fake-hash_algo'
                    expect_image['os_hash_value'] = 'fake-hash_value'
                    mocked_create.return_value = expect_image
                    mocked_get.return_value = expect_image

                    test_shell.do_image_create(self.gc, args)

                    temp_args.pop('file', None)
                    mocked_create.assert_called_once_with(**temp_args)
                    mocked_get.assert_called_once_with('pass')
                    utils.print_dict.assert_called_once_with({
                        'id': 'pass', 'name': 'IMG-01', 'disk_format': 'vhd',
                        'container_format': 'bare',
                        'checksum': 'fake-checksum',
                        'os_hash_algo': 'fake-hash_algo',
                        'os_hash_value': 'fake-hash_value'})
        finally:
            try:
                os.remove(f.name)
            except Exception:
                pass

    @mock.patch('sys.stdin', autospec=True)
    def test_do_image_create_hidden_image(self, mock_stdin):
        args = self._make_args({'name': 'IMG-01', 'disk_format': 'vhd',
                                'container_format': 'bare',
                                'file': None,
                                'os_hidden': True})
        with mock.patch.object(self.gc.images, 'create') as mocked_create:
            ignore_fields = ['self', 'access', 'file', 'schema']
            expect_image = dict([(field, field) for field in ignore_fields])
            expect_image['id'] = 'pass'
            expect_image['name'] = 'IMG-01'
            expect_image['disk_format'] = 'vhd'
            expect_image['container_format'] = 'bare'
            expect_image['os_hidden'] = True
            mocked_create.return_value = expect_image

            # Ensure that the test stdin is not considered
            # to be supplying image data
            mock_stdin.isatty = lambda: True
            test_shell.do_image_create(self.gc, args)

            mocked_create.assert_called_once_with(name='IMG-01',
                                                  disk_format='vhd',
                                                  container_format='bare',
                                                  os_hidden=True)
            utils.print_dict.assert_called_once_with({
                'id': 'pass', 'name': 'IMG-01', 'disk_format': 'vhd',
                'container_format': 'bare', 'os_hidden': True})

    def test_do_image_create_with_file(self):
        self.mock_get_data_file.return_value = six.StringIO()
        try:
            file_name = None
            with open(tempfile.mktemp(), 'w+') as f:
                f.write('Some data here')
                f.flush()
                f.seek(0)
                file_name = f.name
            temp_args = {'name': 'IMG-01',
                         'disk_format': 'vhd',
                         'container_format': 'bare',
                         'file': file_name,
                         'progress': False}
            args = self._make_args(temp_args)
            with mock.patch.object(self.gc.images, 'create') as mocked_create:
                with mock.patch.object(self.gc.images, 'get') as mocked_get:

                    ignore_fields = ['self', 'access', 'schema']
                    expect_image = dict([(field, field) for field in
                                         ignore_fields])
                    expect_image['id'] = 'pass'
                    expect_image['name'] = 'IMG-01'
                    expect_image['disk_format'] = 'vhd'
                    expect_image['container_format'] = 'bare'
                    mocked_create.return_value = expect_image
                    mocked_get.return_value = expect_image

                    test_shell.do_image_create(self.gc, args)

                    temp_args.pop('file', None)
                    mocked_create.assert_called_once_with(**temp_args)
                    mocked_get.assert_called_once_with('pass')
                    utils.print_dict.assert_called_once_with({
                        'id': 'pass', 'name': 'IMG-01', 'disk_format': 'vhd',
                        'container_format': 'bare'})
        finally:
            try:
                os.remove(f.name)
            except Exception:
                pass

    @mock.patch('sys.stdin', autospec=True)
    def test_do_image_create_with_unicode(self, mock_stdin):
        name = u'\u041f\u0420\u0418\u0412\u0415\u0422\u0418\u041a'

        args = self._make_args({'name': name,
                                'file': None})
        with mock.patch.object(self.gc.images, 'create') as mocked_create:
            ignore_fields = ['self', 'access', 'file', 'schema']
            expect_image = dict((field, field) for field in ignore_fields)
            expect_image['id'] = 'pass'
            expect_image['name'] = name
            mocked_create.return_value = expect_image

            mock_stdin.isatty = lambda: True
            test_shell.do_image_create(self.gc, args)

            mocked_create.assert_called_once_with(name=name)
            utils.print_dict.assert_called_once_with({
                'id': 'pass', 'name': name})

    @mock.patch('sys.stdin', autospec=True)
    def test_do_image_create_with_user_props(self, mock_stdin):
        args = self._make_args({'name': 'IMG-01',
                                'property': ['myprop=myval'],
                                'file': None,
                                'container_format': 'bare',
                                'disk_format': 'qcow2'})
        with mock.patch.object(self.gc.images, 'create') as mocked_create:
            ignore_fields = ['self', 'access', 'file', 'schema']
            expect_image = dict([(field, field) for field in ignore_fields])
            expect_image['id'] = 'pass'
            expect_image['name'] = 'IMG-01'
            expect_image['myprop'] = 'myval'
            mocked_create.return_value = expect_image

            # Ensure that the test stdin is not considered
            # to be supplying image data
            mock_stdin.isatty = lambda: True
            test_shell.do_image_create(self.gc, args)

            mocked_create.assert_called_once_with(name='IMG-01',
                                                  myprop='myval',
                                                  container_format='bare',
                                                  disk_format='qcow2')
            utils.print_dict.assert_called_once_with({
                'id': 'pass', 'name': 'IMG-01', 'myprop': 'myval'})

    @mock.patch('glanceclient.common.utils.exit')
    @mock.patch('os.access')
    @mock.patch('sys.stdin', autospec=True)
    def test_neg_do_image_create_no_file_and_stdin_with_store(
            self, mock_stdin, mock_access, mock_utils_exit):
        expected_msg = ('--store option should only be provided with --file '
                        'option or stdin.')
        mock_utils_exit.side_effect = self._mock_utils_exit
        mock_stdin.isatty = lambda: True
        mock_access.return_value = False
        args = self._make_args({'name': 'IMG-01',
                                'property': ['myprop=myval'],
                                'file': None,
                                'store': 'file1',
                                'container_format': 'bare',
                                'disk_format': 'qcow2'})

        try:
            test_shell.do_image_create(self.gc, args)
            self.fail("utils.exit should have been called")
        except SystemExit:
            pass

        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.common.utils.exit')
    def test_neg_do_image_create_invalid_store(
            self, mock_utils_exit):
        expected_msg = ("Store 'dummy' is not valid for this cloud. "
                        "Valid values can be retrieved with stores-info "
                        "command.")
        mock_utils_exit.side_effect = self._mock_utils_exit
        args = self._make_args({'name': 'IMG-01',
                                'property': ['myprop=myval'],
                                'file': "somefile.txt",
                                'store': 'dummy',
                                'container_format': 'bare',
                                'disk_format': 'qcow2'})

        with mock.patch.object(self.gc.images,
                               'get_stores_info') as mock_stores_info:
            mock_stores_info.return_value = self.stores_info_response
            try:
                test_shell.do_image_create(self.gc, args)
                self.fail("utils.exit should have been called")
            except SystemExit:
                pass

        mock_utils_exit.assert_called_once_with(expected_msg)

    # NOTE(rosmaita): have to explicitly set to None the declared but unused
    # arguments (the configparser does that for us normally)
    base_args = {'name': 'Mortimer',
                 'disk_format': 'raw',
                 'container_format': 'bare',
                 'progress': False,
                 'file': None,
                 'uri': None,
                 'import_method': None}

    import_info_response = {'import-methods': {
        'type': 'array',
        'description': 'Import methods available.',
        'value': ['glance-direct', 'web-download']}}

    def _mock_utils_exit(self, msg):
        sys.exit(msg)

    @mock.patch('glanceclient.common.utils.exit')
    @mock.patch('os.access')
    @mock.patch('sys.stdin', autospec=True)
    def test_neg_image_create_via_import_no_method_with_file_and_stdin(
            self, mock_stdin, mock_access, mock_utils_exit):
        expected_msg = ('You cannot use both --file and stdin with the '
                        'glance-direct import method.')
        my_args = self.base_args.copy()
        my_args['file'] = 'some.file'
        args = self._make_args(my_args)
        mock_stdin.isatty = lambda: False
        mock_access.return_value = True
        mock_utils_exit.side_effect = self._mock_utils_exit
        with mock.patch.object(self.gc.images,
                               'get_import_info') as mocked_info:
            mocked_info.return_value = self.import_info_response
            try:
                test_shell.do_image_create_via_import(self.gc, args)
                self.fail("utils.exit should have been called")
            except SystemExit:
                pass
        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.common.utils.exit')
    @mock.patch('os.access')
    @mock.patch('sys.stdin', autospec=True)
    def test_neg_image_create_via_import_no_file_and_stdin_with_store(
            self, mock_stdin, mock_access, mock_utils_exit):
        expected_msg = ('--store option should only be provided with --file '
                        'option or stdin for the glance-direct import method.')
        my_args = self.base_args.copy()
        my_args['import_method'] = 'glance-direct'
        my_args['store'] = 'file1'
        args = self._make_args(my_args)

        mock_stdin.isatty = lambda: True
        mock_access.return_value = False
        mock_utils_exit.side_effect = self._mock_utils_exit
        with mock.patch.object(self.gc.images,
                               'get_import_info') as mocked_info:
            with mock.patch.object(self.gc.images,
                                   'get_stores_info') as mocked_stores_info:
                mocked_stores_info.return_value = self.stores_info_response
                mocked_info.return_value = self.import_info_response
                try:
                    test_shell.do_image_create_via_import(self.gc, args)
                    self.fail("utils.exit should have been called")
                except SystemExit:
                    pass
        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.common.utils.exit')
    @mock.patch('sys.stdin', autospec=True)
    def test_neg_image_create_via_import_no_uri_with_store(
            self, mock_stdin, mock_utils_exit):
        expected_msg = ('--store option should only be provided with --uri '
                        'option for the web-download import method.')
        my_args = self.base_args.copy()
        my_args['import_method'] = 'web-download'
        my_args['store'] = 'file1'
        args = self._make_args(my_args)
        mock_utils_exit.side_effect = self._mock_utils_exit
        with mock.patch.object(self.gc.images,
                               'get_import_info') as mocked_info:
            with mock.patch.object(self.gc.images,
                                   'get_stores_info') as mocked_stores_info:
                mocked_stores_info.return_value = self.stores_info_response
                mocked_info.return_value = self.import_info_response
                try:
                    test_shell.do_image_create_via_import(self.gc, args)
                    self.fail("utils.exit should have been called")
                except SystemExit:
                    pass
        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.common.utils.exit')
    @mock.patch('os.access')
    @mock.patch('sys.stdin', autospec=True)
    def test_neg_image_create_via_import_invalid_store(
            self, mock_stdin, mock_access, mock_utils_exit):
        expected_msg = ("Store 'dummy' is not valid for this cloud. "
                        "Valid values can be retrieved with stores-info"
                        " command.")
        my_args = self.base_args.copy()
        my_args['import_method'] = 'glance-direct'
        my_args['store'] = 'dummy'
        args = self._make_args(my_args)

        mock_stdin.isatty = lambda: True
        mock_access.return_value = False
        mock_utils_exit.side_effect = self._mock_utils_exit
        with mock.patch.object(self.gc.images,
                               'get_import_info') as mocked_info:
            with mock.patch.object(self.gc.images,
                                   'get_stores_info') as mocked_stores_info:
                mocked_stores_info.return_value = self.stores_info_response
                mocked_info.return_value = self.import_info_response
                try:
                    test_shell.do_image_create_via_import(self.gc, args)
                    self.fail("utils.exit should have been called")
                except SystemExit:
                    pass
        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.common.utils.exit')
    @mock.patch('sys.stdin', autospec=True)
    def test_neg_image_create_via_import_no_method_passing_uri(
            self, mock_stdin, mock_utils_exit):
        expected_msg = ('You cannot use --uri without specifying an import '
                        'method.')
        my_args = self.base_args.copy()
        my_args['uri'] = 'http://example.com/whatever'
        args = self._make_args(my_args)
        mock_stdin.isatty = lambda: True
        mock_utils_exit.side_effect = self._mock_utils_exit
        with mock.patch.object(self.gc.images,
                               'get_import_info') as mocked_info:
            mocked_info.return_value = self.import_info_response
            try:
                test_shell.do_image_create_via_import(self.gc, args)
                self.fail("utils.exit should have been called")
            except SystemExit:
                pass
        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.common.utils.exit')
    @mock.patch('sys.stdin', autospec=True)
    def test_neg_image_create_via_import_glance_direct_no_data(
            self, mock_stdin, mock_utils_exit):
        expected_msg = ('You must specify a --file or provide data via stdin '
                        'for the glance-direct import method.')
        my_args = self.base_args.copy()
        my_args['import_method'] = 'glance-direct'
        args = self._make_args(my_args)
        mock_stdin.isatty = lambda: True
        mock_utils_exit.side_effect = self._mock_utils_exit
        with mock.patch.object(self.gc.images,
                               'get_import_info') as mocked_info:
            mocked_info.return_value = self.import_info_response
            try:
                test_shell.do_image_create_via_import(self.gc, args)
                self.fail("utils.exit should have been called")
            except SystemExit:
                pass
        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.common.utils.exit')
    @mock.patch('sys.stdin', autospec=True)
    def test_neg_image_create_via_import_glance_direct_with_uri(
            self, mock_stdin, mock_utils_exit):
        expected_msg = ('You cannot specify a --uri with the glance-direct '
                        'import method.')
        my_args = self.base_args.copy()
        my_args['import_method'] = 'glance-direct'
        my_args['uri'] = 'https://example.com/some/stuff'
        args = self._make_args(my_args)
        mock_stdin.isatty = lambda: True
        mock_utils_exit.side_effect = self._mock_utils_exit
        with mock.patch.object(self.gc.images,
                               'get_import_info') as mocked_info:
            mocked_info.return_value = self.import_info_response
            try:
                test_shell.do_image_create_via_import(self.gc, args)
                self.fail("utils.exit should have been called")
            except SystemExit:
                pass
        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.common.utils.exit')
    @mock.patch('os.access')
    @mock.patch('sys.stdin', autospec=True)
    def test_neg_image_create_via_import_glance_direct_with_file_and_uri(
            self, mock_stdin, mock_access, mock_utils_exit):
        expected_msg = ('You cannot specify a --uri with the glance-direct '
                        'import method.')
        my_args = self.base_args.copy()
        my_args['import_method'] = 'glance-direct'
        my_args['uri'] = 'https://example.com/some/stuff'
        my_args['file'] = 'my.browncow'
        args = self._make_args(my_args)
        mock_stdin.isatty = lambda: True
        mock_access.return_value = True
        mock_utils_exit.side_effect = self._mock_utils_exit
        with mock.patch.object(self.gc.images,
                               'get_import_info') as mocked_info:
            mocked_info.return_value = self.import_info_response
            try:
                test_shell.do_image_create_via_import(self.gc, args)
                self.fail("utils.exit should have been called")
            except SystemExit:
                pass
        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.common.utils.exit')
    @mock.patch('sys.stdin', autospec=True)
    def test_neg_image_create_via_import_glance_direct_with_data_and_uri(
            self, mock_stdin, mock_utils_exit):
        expected_msg = ('You cannot specify a --uri with the glance-direct '
                        'import method.')
        my_args = self.base_args.copy()
        my_args['import_method'] = 'glance-direct'
        my_args['uri'] = 'https://example.com/some/stuff'
        args = self._make_args(my_args)
        mock_stdin.isatty = lambda: False
        mock_utils_exit.side_effect = self._mock_utils_exit
        with mock.patch.object(self.gc.images,
                               'get_import_info') as mocked_info:
            mocked_info.return_value = self.import_info_response
            try:
                test_shell.do_image_create_via_import(self.gc, args)
                self.fail("utils.exit should have been called")
            except SystemExit:
                pass
        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.common.utils.exit')
    @mock.patch('sys.stdin', autospec=True)
    def test_neg_image_create_via_import_web_download_no_uri(
            self, mock_stdin, mock_utils_exit):
        expected_msg = ('URI is required for web-download import method. '
                        'Please use \'--uri <uri>\'.')
        my_args = self.base_args.copy()
        my_args['import_method'] = 'web-download'
        args = self._make_args(my_args)
        mock_stdin.isatty = lambda: True
        mock_utils_exit.side_effect = self._mock_utils_exit
        with mock.patch.object(self.gc.images,
                               'get_import_info') as mocked_info:
            mocked_info.return_value = self.import_info_response
            try:
                test_shell.do_image_create_via_import(self.gc, args)
                self.fail("utils.exit should have been called")
            except SystemExit:
                pass
        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.common.utils.exit')
    @mock.patch('sys.stdin', autospec=True)
    def test_neg_image_create_via_import_web_download_no_uri_with_file(
            self, mock_stdin, mock_utils_exit):
        expected_msg = ('URI is required for web-download import method. '
                        'Please use \'--uri <uri>\'.')
        my_args = self.base_args.copy()
        my_args['import_method'] = 'web-download'
        my_args['file'] = 'my.browncow'
        args = self._make_args(my_args)
        mock_stdin.isatty = lambda: True
        mock_utils_exit.side_effect = self._mock_utils_exit
        with mock.patch.object(self.gc.images,
                               'get_import_info') as mocked_info:
            mocked_info.return_value = self.import_info_response
            try:
                test_shell.do_image_create_via_import(self.gc, args)
                self.fail("utils.exit should have been called")
            except SystemExit:
                pass
        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.common.utils.exit')
    @mock.patch('sys.stdin', autospec=True)
    def test_neg_image_create_via_import_web_download_no_uri_with_data(
            self, mock_stdin, mock_utils_exit):
        expected_msg = ('URI is required for web-download import method. '
                        'Please use \'--uri <uri>\'.')
        my_args = self.base_args.copy()
        my_args['import_method'] = 'web-download'
        my_args['file'] = 'my.browncow'
        args = self._make_args(my_args)
        mock_stdin.isatty = lambda: False
        mock_utils_exit.side_effect = self._mock_utils_exit
        with mock.patch.object(self.gc.images,
                               'get_import_info') as mocked_info:
            mocked_info.return_value = self.import_info_response
            try:
                test_shell.do_image_create_via_import(self.gc, args)
                self.fail("utils.exit should have been called")
            except SystemExit:
                pass
        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.common.utils.exit')
    @mock.patch('sys.stdin', autospec=True)
    def test_neg_image_create_via_import_web_download_with_data_and_uri(
            self, mock_stdin, mock_utils_exit):
        expected_msg = ('You cannot pass data via stdin with the web-download '
                        'import method.')
        my_args = self.base_args.copy()
        my_args['import_method'] = 'web-download'
        my_args['uri'] = 'https://example.com/some/stuff'
        args = self._make_args(my_args)
        mock_stdin.isatty = lambda: False
        mock_utils_exit.side_effect = self._mock_utils_exit
        with mock.patch.object(self.gc.images,
                               'get_import_info') as mocked_info:
            mocked_info.return_value = self.import_info_response
            try:
                test_shell.do_image_create_via_import(self.gc, args)
                self.fail("utils.exit should have been called")
            except SystemExit:
                pass
        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.common.utils.exit')
    @mock.patch('sys.stdin', autospec=True)
    def test_neg_image_create_via_import_web_download_with_file_and_uri(
            self, mock_stdin, mock_utils_exit):
        expected_msg = ('You cannot specify a --file with the web-download '
                        'import method.')
        my_args = self.base_args.copy()
        my_args['import_method'] = 'web-download'
        my_args['uri'] = 'https://example.com/some/stuff'
        my_args['file'] = 'my.browncow'
        args = self._make_args(my_args)
        mock_stdin.isatty = lambda: True
        mock_utils_exit.side_effect = self._mock_utils_exit
        with mock.patch.object(self.gc.images,
                               'get_import_info') as mocked_info:
            mocked_info.return_value = self.import_info_response
            try:
                test_shell.do_image_create_via_import(self.gc, args)
                self.fail("utils.exit should have been called")
            except SystemExit:
                pass
        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.common.utils.exit')
    @mock.patch('sys.stdin', autospec=True)
    def test_neg_image_create_via_import_bad_method(
            self, mock_stdin, mock_utils_exit):
        expected_msg = ('Import method \'swift-party-time\' is not valid '
                        'for this cloud. Valid values can be retrieved with '
                        'import-info command.')
        my_args = self.base_args.copy()
        my_args['import_method'] = 'swift-party-time'
        args = self._make_args(my_args)
        mock_stdin.isatty = lambda: True
        mock_utils_exit.side_effect = self._mock_utils_exit
        with mock.patch.object(self.gc.images,
                               'get_import_info') as mocked_info:
            mocked_info.return_value = self.import_info_response
            try:
                test_shell.do_image_create_via_import(self.gc, args)
                self.fail("utils.exit should have been called")
            except SystemExit:
                pass
        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.common.utils.exit')
    @mock.patch('sys.stdin', autospec=True)
    def test_neg_image_create_via_import_no_method_with_data_and_method_NA(
            self, mock_stdin, mock_utils_exit):
        expected_msg = ('Import method \'glance-direct\' is not valid '
                        'for this cloud. Valid values can be retrieved with '
                        'import-info command.')
        args = self._make_args(self.base_args)
        # need to fake some data, or this is "just like" a
        # create-image-record-only call
        mock_stdin.isatty = lambda: False
        mock_utils_exit.side_effect = self._mock_utils_exit
        my_import_info_response = deepcopy(self.import_info_response)
        my_import_info_response['import-methods']['value'] = ['web-download']
        with mock.patch.object(self.gc.images,
                               'get_import_info') as mocked_info:
            mocked_info.return_value = my_import_info_response
            try:
                test_shell.do_image_create_via_import(self.gc, args)
                self.fail("utils.exit should have been called")
            except SystemExit:
                pass
        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.common.utils.exit')
    @mock.patch('sys.stdin', autospec=True)
    def test_neg_image_create_via_import_good_method_not_available(
            self, mock_stdin, mock_utils_exit):
        """Make sure the good method names aren't hard coded somewhere"""
        expected_msg = ('Import method \'glance-direct\' is not valid for '
                        'this cloud. Valid values can be retrieved with '
                        'import-info command.')
        my_args = self.base_args.copy()
        my_args['import_method'] = 'glance-direct'
        args = self._make_args(my_args)
        mock_stdin.isatty = lambda: True
        mock_utils_exit.side_effect = self._mock_utils_exit
        my_import_info_response = deepcopy(self.import_info_response)
        my_import_info_response['import-methods']['value'] = ['bad-bad-method']
        with mock.patch.object(self.gc.images,
                               'get_import_info') as mocked_info:
            mocked_info.return_value = my_import_info_response
            try:
                test_shell.do_image_create_via_import(self.gc, args)
                self.fail("utils.exit should have been called")
            except SystemExit:
                pass
        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.v2.shell.do_image_import')
    @mock.patch('glanceclient.v2.shell.do_image_stage')
    @mock.patch('sys.stdin', autospec=True)
    def test_image_create_via_import_no_method_with_stdin(
            self, mock_stdin, mock_do_stage, mock_do_import):
        """Backward compat -> handle this like a glance-direct"""
        mock_stdin.isatty = lambda: False
        self.mock_get_data_file.return_value = six.StringIO()
        args = self._make_args(self.base_args)
        with mock.patch.object(self.gc.images, 'create') as mocked_create:
            with mock.patch.object(self.gc.images, 'get') as mocked_get:
                with mock.patch.object(self.gc.images,
                                       'get_import_info') as mocked_info:

                    ignore_fields = ['self', 'access', 'schema']
                    expect_image = dict([(field, field) for field in
                                         ignore_fields])
                    expect_image['id'] = 'via-stdin'
                    expect_image['name'] = 'Mortimer'
                    expect_image['disk_format'] = 'raw'
                    expect_image['container_format'] = 'bare'
                    mocked_create.return_value = expect_image
                    mocked_get.return_value = expect_image
                    mocked_info.return_value = self.import_info_response

                    test_shell.do_image_create_via_import(self.gc, args)
                    mocked_create.assert_called_once()
                    mock_do_stage.assert_called_once()
                    mock_do_import.assert_called_once()
                    mocked_get.assert_called_with('via-stdin')
                    utils.print_dict.assert_called_with({
                        'id': 'via-stdin', 'name': 'Mortimer',
                        'disk_format': 'raw', 'container_format': 'bare'})

    @mock.patch('glanceclient.v2.shell.do_image_import')
    @mock.patch('glanceclient.v2.shell.do_image_stage')
    @mock.patch('os.access')
    @mock.patch('sys.stdin', autospec=True)
    def test_image_create_via_import_no_method_passing_file(
            self, mock_stdin, mock_access, mock_do_stage, mock_do_import):
        """Backward compat -> handle this like a glance-direct"""
        mock_stdin.isatty = lambda: True
        self.mock_get_data_file.return_value = six.StringIO()
        mock_access.return_value = True
        my_args = self.base_args.copy()
        my_args['file'] = 'fake-image-file.browncow'
        args = self._make_args(my_args)
        with mock.patch.object(self.gc.images, 'create') as mocked_create:
            with mock.patch.object(self.gc.images, 'get') as mocked_get:
                with mock.patch.object(self.gc.images,
                                       'get_import_info') as mocked_info:

                    ignore_fields = ['self', 'access', 'schema']
                    expect_image = dict([(field, field) for field in
                                         ignore_fields])
                    expect_image['id'] = 'via-file'
                    expect_image['name'] = 'Mortimer'
                    expect_image['disk_format'] = 'raw'
                    expect_image['container_format'] = 'bare'
                    mocked_create.return_value = expect_image
                    mocked_get.return_value = expect_image
                    mocked_info.return_value = self.import_info_response

                    test_shell.do_image_create_via_import(self.gc, args)
                    mocked_create.assert_called_once()
                    mock_do_stage.assert_called_once()
                    mock_do_import.assert_called_once()
                    mocked_get.assert_called_with('via-file')
                    utils.print_dict.assert_called_with({
                        'id': 'via-file', 'name': 'Mortimer',
                        'disk_format': 'raw', 'container_format': 'bare'})

    @mock.patch('glanceclient.v2.shell.do_image_import')
    @mock.patch('glanceclient.v2.shell.do_image_stage')
    @mock.patch('sys.stdin', autospec=True)
    def test_do_image_create_via_import_with_no_method_no_data(
            self, mock_stdin, mock_do_image_stage, mock_do_image_import):
        """Create an image record without calling do_stage or do_import"""
        img_create_args = {'name': 'IMG-11',
                           'os_architecture': 'powerpc',
                           'id': 'watch-out-for-ossn-0075',
                           'progress': False}
        client_args = {'import_method': None,
                       'file': None,
                       'uri': None}
        temp_args = img_create_args.copy()
        temp_args.update(client_args)
        args = self._make_args(temp_args)
        with mock.patch.object(self.gc.images, 'create') as mocked_create:
            with mock.patch.object(self.gc.images, 'get') as mocked_get:
                with mock.patch.object(self.gc.images,
                                       'get_import_info') as mocked_info:

                    ignore_fields = ['self', 'access', 'schema']
                    expect_image = dict([(field, field) for field in
                                         ignore_fields])
                    expect_image['name'] = 'IMG-11'
                    expect_image['id'] = 'watch-out-for-ossn-0075'
                    expect_image['os_architecture'] = 'powerpc'
                    mocked_create.return_value = expect_image
                    mocked_get.return_value = expect_image
                    mocked_info.return_value = self.import_info_response
                    mock_stdin.isatty = lambda: True

                    test_shell.do_image_create_via_import(self.gc, args)
                    mocked_create.assert_called_once_with(**img_create_args)
                    mocked_get.assert_called_with('watch-out-for-ossn-0075')
                    mock_do_image_stage.assert_not_called()
                    mock_do_image_import.assert_not_called()
                    utils.print_dict.assert_called_with({
                        'name': 'IMG-11', 'os_architecture': 'powerpc',
                        'id': 'watch-out-for-ossn-0075'})

    @mock.patch('glanceclient.v2.shell.do_image_import')
    @mock.patch('glanceclient.v2.shell.do_image_stage')
    @mock.patch('sys.stdin', autospec=True)
    def test_do_image_create_via_import_with_web_download(
            self, mock_stdin, mock_do_image_stage, mock_do_image_import):
        temp_args = {'name': 'IMG-01',
                     'disk_format': 'vhd',
                     'container_format': 'bare',
                     'uri': 'http://example.com/image.qcow',
                     'import_method': 'web-download',
                     'progress': False}
        args = self._make_args(temp_args)
        with mock.patch.object(self.gc.images, 'create') as mocked_create:
            with mock.patch.object(self.gc.images, 'get') as mocked_get:
                with mock.patch.object(self.gc.images,
                                       'get_import_info') as mocked_info:

                    ignore_fields = ['self', 'access', 'schema']
                    expect_image = dict([(field, field) for field in
                                         ignore_fields])
                    expect_image['id'] = 'pass'
                    expect_image['name'] = 'IMG-01'
                    expect_image['disk_format'] = 'vhd'
                    expect_image['container_format'] = 'bare'
                    expect_image['status'] = 'queued'
                    mocked_create.return_value = expect_image
                    mocked_get.return_value = expect_image
                    mocked_info.return_value = self.import_info_response
                    mock_stdin.isatty = lambda: True

                    test_shell.do_image_create_via_import(self.gc, args)
                    mock_do_image_stage.assert_not_called()
                    mock_do_image_import.assert_called_once()
                    mocked_create.assert_called_once_with(**temp_args)
                    mocked_get.assert_called_with('pass')
                    utils.print_dict.assert_called_with({
                        'id': 'pass', 'name': 'IMG-01', 'disk_format': 'vhd',
                        'container_format': 'bare', 'status': 'queued'})

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

    def test_do_image_update_hide_image(self):
        args = self._make_args({'id': 'pass', 'os_hidden': 'true'})
        with mock.patch.object(self.gc.images, 'update') as mocked_update:
            ignore_fields = ['self', 'access', 'file', 'schema']
            expect_image = dict([(field, field) for field in ignore_fields])
            expect_image['id'] = 'pass'
            expect_image['name'] = 'IMG-01'
            expect_image['disk_format'] = 'vhd'
            expect_image['container_format'] = 'bare'
            expect_image['os_hidden'] = True
            mocked_update.return_value = expect_image

            test_shell.do_image_update(self.gc, args)

            mocked_update.assert_called_once_with('pass',
                                                  None,
                                                  os_hidden='true')
            utils.print_dict.assert_called_once_with({
                'id': 'pass', 'name': 'IMG-01', 'disk_format': 'vhd',
                'container_format': 'bare', 'os_hidden': True})

    def test_do_image_update_revert_hide_image(self):
        args = self._make_args({'id': 'pass', 'os_hidden': 'false'})
        with mock.patch.object(self.gc.images, 'update') as mocked_update:
            ignore_fields = ['self', 'access', 'file', 'schema']
            expect_image = dict([(field, field) for field in ignore_fields])
            expect_image['id'] = 'pass'
            expect_image['name'] = 'IMG-01'
            expect_image['disk_format'] = 'vhd'
            expect_image['container_format'] = 'bare'
            expect_image['os_hidden'] = False
            mocked_update.return_value = expect_image

            test_shell.do_image_update(self.gc, args)

            mocked_update.assert_called_once_with('pass',
                                                  None,
                                                  os_hidden='false')
            utils.print_dict.assert_called_once_with({
                'id': 'pass', 'name': 'IMG-01', 'disk_format': 'vhd',
                'container_format': 'bare', 'os_hidden': False})

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

    def test_do_location_add(self):
        gc = self.gc
        loc = {'url': 'http://foo.com/',
               'metadata': {'foo': 'bar'},
               'validation_data': {'checksum': 'csum',
                                   'os_hash_algo': 'algo',
                                   'os_hash_value': 'value'}}
        args = {'id': 'pass',
                'url': loc['url'],
                'metadata': json.dumps(loc['metadata']),
                'checksum': 'csum',
                'hash_algo': 'algo',
                'hash_value': 'value'}
        with mock.patch.object(gc.images, 'add_location') as mocked_addloc:
            expect_image = {'id': 'pass', 'locations': [loc]}
            mocked_addloc.return_value = expect_image

            test_shell.do_location_add(self.gc, self._make_args(args))
            mocked_addloc.assert_called_once_with(
                'pass', loc['url'], loc['metadata'],
                validation_data=loc['validation_data'])
            utils.print_dict.assert_called_once_with(expect_image)

    def test_do_location_delete(self):
        gc = self.gc
        loc_set = set(['http://foo/bar', 'http://spam/ham'])
        args = self._make_args({'id': 'pass', 'url': loc_set})

        with mock.patch.object(gc.images, 'delete_locations') as mocked_rmloc:
            test_shell.do_location_delete(self.gc, args)
            mocked_rmloc.assert_called_once_with('pass', loc_set)

    def test_do_location_update(self):
        gc = self.gc
        loc = {'url': 'http://foo.com/', 'metadata': {'foo': 'bar'}}
        args = self._make_args({'id': 'pass',
                                'url': loc['url'],
                                'metadata': json.dumps(loc['metadata'])})
        with mock.patch.object(gc.images, 'update_location') as mocked_modloc:
            expect_image = {'id': 'pass', 'locations': [loc]}
            mocked_modloc.return_value = expect_image

            test_shell.do_location_update(self.gc, args)
            mocked_modloc.assert_called_once_with('pass',
                                                  loc['url'],
                                                  loc['metadata'])
            utils.print_dict.assert_called_once_with(expect_image)

    def test_image_upload(self):
        args = self._make_args(
            {'id': 'IMG-01', 'file': 'test', 'size': 1024, 'progress': False})

        with mock.patch.object(self.gc.images, 'upload') as mocked_upload:
            utils.get_data_file = mock.Mock(return_value='testfile')
            mocked_upload.return_value = None
            test_shell.do_image_upload(self.gc, args)
            mocked_upload.assert_called_once_with('IMG-01', 'testfile', 1024,
                                                  backend=None)

    @mock.patch('glanceclient.common.utils.exit')
    def test_image_upload_invalid_store(self, mock_utils_exit):
        expected_msg = ("Store 'dummy' is not valid for this cloud. "
                        "Valid values can be retrieved with stores-info "
                        "command.")
        mock_utils_exit.side_effect = self._mock_utils_exit

        args = self._make_args(
            {'id': 'IMG-01', 'file': 'test', 'size': 1024, 'progress': False,
             'store': 'dummy'})

        with mock.patch.object(self.gc.images,
                               'get_stores_info') as mock_stores_info:
            mock_stores_info.return_value = self.stores_info_response
            try:
                test_shell.do_image_upload(self.gc, args)
                self.fail("utils.exit should have been called")
            except SystemExit:
                pass

        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.common.utils.exit')
    def test_neg_image_import_not_available(self, mock_utils_exit):
        expected_msg = 'Target Glance does not support Image Import workflow'
        mock_utils_exit.side_effect = self._mock_utils_exit
        args = self._make_args(
            {'id': 'IMG-01', 'import_method': 'smarty-pants', 'uri': None})
        with mock.patch.object(self.gc.images, 'import') as mocked_import:
            with mock.patch.object(self.gc.images,
                                   'get_import_info') as mocked_info:
                mocked_info.side_effect = exc.HTTPNotFound
                try:
                    test_shell.do_image_import(self.gc, args)
                    self.fail("utils.exit should have been called")
                except SystemExit:
                    pass
        mock_utils_exit.assert_called_once_with(expected_msg)
        mocked_import.assert_not_called()

    @mock.patch('glanceclient.common.utils.exit')
    def test_neg_image_import_bad_method(self, mock_utils_exit):
        expected_msg = ('Import method \'smarty-pants\' is not valid for this '
                        'cloud. Valid values can be retrieved with '
                        'import-info command.')
        mock_utils_exit.side_effect = self._mock_utils_exit
        args = self._make_args(
            {'id': 'IMG-01', 'import_method': 'smarty-pants', 'uri': None})
        with mock.patch.object(self.gc.images,
                               'get_import_info') as mocked_info:
            mocked_info.return_value = self.import_info_response
            try:
                test_shell.do_image_import(self.gc, args)
                self.fail("utils.exit should have been called")
            except SystemExit:
                pass
        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.common.utils.exit')
    def test_neg_image_import_no_methods_configured(self, mock_utils_exit):
        expected_msg = ('Import method \'glance-direct\' is not valid for '
                        'this cloud. Valid values can be retrieved with '
                        'import-info command.')
        mock_utils_exit.side_effect = self._mock_utils_exit
        args = self._make_args(
            {'id': 'IMG-01', 'import_method': 'glance-direct', 'uri': None})
        with mock.patch.object(self.gc.images,
                               'get_import_info') as mocked_info:
            mocked_info.return_value = {"import-methods": {"value": []}}
            try:
                test_shell.do_image_import(self.gc, args)
                self.fail("utils.exit should have been called")
            except SystemExit:
                pass
        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.common.utils.exit')
    def test_neg_image_import_glance_direct_image_not_uploading_status(
            self, mock_utils_exit):
        expected_msg = ('The \'glance-direct\' import method can only be '
                        'applied to an image in status \'uploading\'')
        mock_utils_exit.side_effect = self._mock_utils_exit
        args = self._make_args(
            {'id': 'IMG-01', 'import_method': 'glance-direct', 'uri': None})
        with mock.patch.object(self.gc.images,
                               'get_import_info') as mocked_info:
            with mock.patch.object(self.gc.images, 'get') as mocked_get:
                mocked_get.return_value = {'status': 'queued',
                                           'container_format': 'bare',
                                           'disk_format': 'raw'}
                mocked_info.return_value = self.import_info_response
                try:
                    test_shell.do_image_import(self.gc, args)
                    self.fail("utils.exit should have been called")
                except SystemExit:
                    pass
        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.common.utils.exit')
    def test_neg_image_import_web_download_image_not_queued_status(
            self, mock_utils_exit):
        expected_msg = ('The \'web-download\' import method can only be '
                        'applied to an image in status \'queued\'')
        mock_utils_exit.side_effect = self._mock_utils_exit
        args = self._make_args(
            {'id': 'IMG-01', 'import_method': 'web-download',
             'uri': 'http://joes-image-shack.com/funky.qcow2'})
        with mock.patch.object(self.gc.images,
                               'get_import_info') as mocked_info:
            with mock.patch.object(self.gc.images, 'get') as mocked_get:
                mocked_get.return_value = {'status': 'uploading',
                                           'container_format': 'bare',
                                           'disk_format': 'raw'}
                mocked_info.return_value = self.import_info_response
                try:
                    test_shell.do_image_import(self.gc, args)
                    self.fail("utils.exit should have been called")
                except SystemExit:
                    pass
        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.common.utils.exit')
    def test_neg_image_import_image_no_container_format(
            self, mock_utils_exit):
        expected_msg = ('The \'container_format\' and \'disk_format\' '
                        'properties must be set on an image before it can be '
                        'imported.')
        mock_utils_exit.side_effect = self._mock_utils_exit
        args = self._make_args(
            {'id': 'IMG-01', 'import_method': 'web-download',
             'uri': 'http://joes-image-shack.com/funky.qcow2'})
        with mock.patch.object(self.gc.images,
                               'get_import_info') as mocked_info:
            with mock.patch.object(self.gc.images, 'get') as mocked_get:
                mocked_get.return_value = {'status': 'uploading',
                                           'disk_format': 'raw'}
                mocked_info.return_value = self.import_info_response
                try:
                    test_shell.do_image_import(self.gc, args)
                    self.fail("utils.exit should have been called")
                except SystemExit:
                    pass
        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.common.utils.exit')
    def test_neg_image_import_image_no_disk_format(
            self, mock_utils_exit):
        expected_msg = ('The \'container_format\' and \'disk_format\' '
                        'properties must be set on an image before it can be '
                        'imported.')
        mock_utils_exit.side_effect = self._mock_utils_exit
        args = self._make_args(
            {'id': 'IMG-01', 'import_method': 'web-download',
             'uri': 'http://joes-image-shack.com/funky.qcow2'})
        with mock.patch.object(self.gc.images,
                               'get_import_info') as mocked_info:
            with mock.patch.object(self.gc.images, 'get') as mocked_get:
                mocked_get.return_value = {'status': 'uploading',
                                           'container_format': 'bare'}
                mocked_info.return_value = self.import_info_response
                try:
                    test_shell.do_image_import(self.gc, args)
                    self.fail("utils.exit should have been called")
                except SystemExit:
                    pass
        mock_utils_exit.assert_called_once_with(expected_msg)

    @mock.patch('glanceclient.common.utils.exit')
    def test_image_import_invalid_store(self, mock_utils_exit):
        expected_msg = ("Store 'dummy' is not valid for this cloud. "
                        "Valid values can be retrieved with stores-info "
                        "command.")
        mock_utils_exit.side_effect = self._mock_utils_exit

        args = self._make_args(
            {'id': 'IMG-01', 'import_method': 'glance-direct', 'uri': None,
             'store': 'dummy'})

        with mock.patch.object(self.gc.images, 'get') as mocked_get:
            with mock.patch.object(self.gc.images,
                                   'get_import_info') as mocked_info:
                mocked_get.return_value = {'status': 'uploading',
                                           'container_format': 'bare',
                                           'disk_format': 'raw'}
                with mock.patch.object(self.gc.images,
                                       'get_stores_info') as mock_stores_info:
                    mocked_info.return_value = self.import_info_response
                    mock_stores_info.return_value = self.stores_info_response
                    try:
                        test_shell.do_image_import(self.gc, args)
                        self.fail("utils.exit should have been called")
                    except SystemExit:
                        pass

        mock_utils_exit.assert_called_once_with(expected_msg)

    def test_image_import_glance_direct(self):
        args = self._make_args(
            {'id': 'IMG-01', 'import_method': 'glance-direct', 'uri': None})
        with mock.patch.object(self.gc.images, 'image_import') as mock_import:
            with mock.patch.object(self.gc.images, 'get') as mocked_get:
                with mock.patch.object(self.gc.images,
                                       'get_import_info') as mocked_info:
                    mocked_get.return_value = {'status': 'uploading',
                                               'container_format': 'bare',
                                               'disk_format': 'raw'}
                    mocked_info.return_value = self.import_info_response
                    mock_import.return_value = None
                    test_shell.do_image_import(self.gc, args)
                    mock_import.assert_called_once_with(
                        'IMG-01', 'glance-direct', None, backend=None)

    def test_image_import_web_download(self):
        args = self._make_args(
            {'id': 'IMG-01', 'uri': 'http://example.com/image.qcow',
             'import_method': 'web-download'})
        with mock.patch.object(self.gc.images, 'image_import') as mock_import:
            with mock.patch.object(self.gc.images, 'get') as mocked_get:
                with mock.patch.object(self.gc.images,
                                       'get_import_info') as mocked_info:
                    mocked_get.return_value = {'status': 'queued',
                                               'container_format': 'bare',
                                               'disk_format': 'raw'}
                    mocked_info.return_value = self.import_info_response
                    mock_import.return_value = None
                    test_shell.do_image_import(self.gc, args)
                    mock_import.assert_called_once_with(
                        'IMG-01', 'web-download',
                        'http://example.com/image.qcow', backend=None)

    @mock.patch('glanceclient.common.utils.print_image')
    def test_image_import_no_print_image(self, mocked_utils_print_image):
        args = self._make_args(
            {'id': 'IMG-02', 'uri': None, 'import_method': 'glance-direct',
             'from_create': True})
        with mock.patch.object(self.gc.images, 'image_import') as mock_import:
            with mock.patch.object(self.gc.images, 'get') as mocked_get:
                with mock.patch.object(self.gc.images,
                                       'get_import_info') as mocked_info:
                    mocked_get.return_value = {'status': 'uploading',
                                               'container_format': 'bare',
                                               'disk_format': 'raw'}
                    mocked_info.return_value = self.import_info_response
                    mock_import.return_value = None
                    test_shell.do_image_import(self.gc, args)
                    mock_import.assert_called_once_with(
                        'IMG-02', 'glance-direct', None, backend=None)
                    mocked_utils_print_image.assert_not_called()

    def test_image_download(self):
        args = self._make_args(
            {'id': 'IMG-01', 'file': 'test', 'progress': True,
             'allow_md5_fallback': False})

        with mock.patch.object(self.gc.images, 'data') as mocked_data, \
                mock.patch.object(utils, '_extract_request_id'):
            mocked_data.return_value = utils.RequestIdProxy(
                [c for c in 'abcdef'])

            test_shell.do_image_download(self.gc, args)
            mocked_data.assert_called_once_with('IMG-01',
                                                allow_md5_fallback=False)

        # check that non-default value is being passed correctly
        args.allow_md5_fallback = True
        with mock.patch.object(self.gc.images, 'data') as mocked_data, \
                mock.patch.object(utils, '_extract_request_id'):
            mocked_data.return_value = utils.RequestIdProxy(
                [c for c in 'abcdef'])

            test_shell.do_image_download(self.gc, args)
            mocked_data.assert_called_once_with('IMG-01',
                                                allow_md5_fallback=True)

    @mock.patch.object(utils, 'exit')
    @mock.patch('sys.stdout', autospec=True)
    def test_image_download_no_file_arg(self, mocked_stdout,
                                        mocked_utils_exit):
        # Indicate that no file name was given as command line argument
        args = self._make_args({'id': '1234', 'file': None, 'progress': False,
                                'allow_md5_fallback': False})
        # Indicate that no file is specified for output redirection
        mocked_stdout.isatty = lambda: True
        test_shell.do_image_download(self.gc, args)
        mocked_utils_exit.assert_called_once_with(
            'No redirection or local file specified for downloaded image'
            ' data. Please specify a local file with --file to save'
            ' downloaded image or redirect output to another source.')

    def test_do_image_delete(self):
        args = argparse.Namespace(id=['image1', 'image2'])
        with mock.patch.object(self.gc.images, 'delete') as mocked_delete:
            mocked_delete.return_value = 0

            test_shell.do_image_delete(self.gc, args)
            self.assertEqual(2, mocked_delete.call_count)

    def test_do_image_deactivate(self):
        args = argparse.Namespace(id='image1')
        with mock.patch.object(self.gc.images,
                               'deactivate') as mocked_deactivate:
            mocked_deactivate.return_value = 0

            test_shell.do_image_deactivate(self.gc, args)
            self.assertEqual(1, mocked_deactivate.call_count)

    def test_do_image_reactivate(self):
        args = argparse.Namespace(id='image1')
        with mock.patch.object(self.gc.images,
                               'reactivate') as mocked_reactivate:
            mocked_reactivate.return_value = 0

            test_shell.do_image_reactivate(self.gc, args)
            self.assertEqual(1, mocked_reactivate.call_count)

    @mock.patch.object(utils, 'exit')
    @mock.patch.object(utils, 'print_err')
    def test_do_image_delete_with_invalid_ids(self, mocked_print_err,
                                              mocked_utils_exit):
        args = argparse.Namespace(id=['image1', 'image2'])
        with mock.patch.object(self.gc.images, 'delete') as mocked_delete:
            mocked_delete.side_effect = exc.HTTPNotFound

            test_shell.do_image_delete(self.gc, args)

            self.assertEqual(2, mocked_delete.call_count)
            self.assertEqual(2, mocked_print_err.call_count)
            mocked_utils_exit.assert_called_once_with()

    @mock.patch.object(utils, 'exit')
    @mock.patch.object(utils, 'print_err')
    def test_do_image_delete_with_forbidden_ids(self, mocked_print_err,
                                                mocked_utils_exit):
        args = argparse.Namespace(id=['image1', 'image2'])
        with mock.patch.object(self.gc.images, 'delete') as mocked_delete:
            mocked_delete.side_effect = exc.HTTPForbidden

            test_shell.do_image_delete(self.gc, args)

            self.assertEqual(2, mocked_delete.call_count)
            self.assertEqual(2, mocked_print_err.call_count)
            mocked_utils_exit.assert_called_once_with()

    @mock.patch.object(utils, 'exit')
    @mock.patch.object(utils, 'print_err')
    def test_do_image_delete_with_image_in_use(self, mocked_print_err,
                                               mocked_utils_exit):
        args = argparse.Namespace(id=['image1', 'image2'])
        with mock.patch.object(self.gc.images, 'delete') as mocked_delete:
            mocked_delete.side_effect = exc.HTTPConflict

            test_shell.do_image_delete(self.gc, args)

            self.assertEqual(2, mocked_delete.call_count)
            self.assertEqual(2, mocked_print_err.call_count)
            mocked_utils_exit.assert_called_once_with()

    def test_do_image_delete_deleted(self):
        image_id = 'deleted-img'
        args = argparse.Namespace(id=[image_id])
        with mock.patch.object(self.gc.images, 'delete') as mocked_delete:
            mocked_delete.side_effect = exc.HTTPNotFound

            self.assert_exits_with_msg(func=test_shell.do_image_delete,
                                       func_args=args)

    @mock.patch('sys.stdout', autospec=True)
    @mock.patch.object(utils, 'print_err')
    def test_do_image_download_with_forbidden_id(self, mocked_print_err,
                                                 mocked_stdout):
        args = self._make_args({'id': 'IMG-01', 'file': None,
                                'progress': False,
                                'allow_md5_fallback': False})
        mocked_stdout.isatty = lambda: False
        with mock.patch.object(self.gc.images, 'data') as mocked_data:
            mocked_data.side_effect = exc.HTTPForbidden
            try:
                test_shell.do_image_download(self.gc, args)
                self.fail('Exit not called')
            except SystemExit:
                pass

            self.assertEqual(1, mocked_data.call_count)
            self.assertEqual(1, mocked_print_err.call_count)

    @mock.patch('sys.stdout', autospec=True)
    @mock.patch.object(utils, 'print_err')
    def test_do_image_download_with_500(self, mocked_print_err, mocked_stdout):
        args = self._make_args({'id': 'IMG-01', 'file': None,
                                'progress': False,
                                'allow_md5_fallback': False})
        mocked_stdout.isatty = lambda: False
        with mock.patch.object(self.gc.images, 'data') as mocked_data:
            mocked_data.side_effect = exc.HTTPInternalServerError
            try:
                test_shell.do_image_download(self.gc, args)
                self.fail('Exit not called')
            except SystemExit:
                pass

            self.assertEqual(1, mocked_data.call_count)
            self.assertEqual(1, mocked_print_err.call_count)

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

        self.assert_exits_with_msg(func=test_shell.do_member_create,
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

        self.assert_exits_with_msg(func=test_shell.do_member_update,
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

        self.assert_exits_with_msg(func=test_shell.do_member_delete,
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

        self.assert_exits_with_msg(func=test_shell.do_image_tag_update,
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

        self.assert_exits_with_msg(func=test_shell.do_image_tag_delete,
                                   func_args=args,
                                   err_msg=msg)

    def test_do_md_namespace_create(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'protected': True})
        with mock.patch.object(self.gc.metadefs_namespace,
                               'create') as mocked_create:
            expect_namespace = {
                'namespace': 'MyNamespace',
                'protected': True
            }

            mocked_create.return_value = expect_namespace

            test_shell.do_md_namespace_create(self.gc, args)

            mocked_create.assert_called_once_with(namespace='MyNamespace',
                                                  protected=True)
            utils.print_dict.assert_called_once_with(expect_namespace)

    def test_do_md_namespace_import(self):
        args = self._make_args({'file': 'test'})

        expect_namespace = {
            'namespace': 'MyNamespace',
            'protected': True
        }

        with mock.patch.object(self.gc.metadefs_namespace,
                               'create') as mocked_create:
            mock_read = mock.Mock(return_value=json.dumps(expect_namespace))
            mock_file = mock.Mock(read=mock_read)
            utils.get_data_file = mock.Mock(return_value=mock_file)
            mocked_create.return_value = expect_namespace

            test_shell.do_md_namespace_import(self.gc, args)

            mocked_create.assert_called_once_with(**expect_namespace)
            utils.print_dict.assert_called_once_with(expect_namespace)

    def test_do_md_namespace_import_invalid_json(self):
        args = self._make_args({'file': 'test'})
        mock_read = mock.Mock(return_value='Invalid')
        mock_file = mock.Mock(read=mock_read)
        utils.get_data_file = mock.Mock(return_value=mock_file)

        self.assertRaises(SystemExit, test_shell.do_md_namespace_import,
                          self.gc, args)

    def test_do_md_namespace_import_no_input(self):
        args = self._make_args({'file': None})
        utils.get_data_file = mock.Mock(return_value=None)

        self.assertRaises(SystemExit, test_shell.do_md_namespace_import,
                          self.gc, args)

    def test_do_md_namespace_update(self):
        args = self._make_args({'id': 'MyNamespace',
                                'protected': True})
        with mock.patch.object(self.gc.metadefs_namespace,
                               'update') as mocked_update:
            expect_namespace = {
                'namespace': 'MyNamespace',
                'protected': True
            }

            mocked_update.return_value = expect_namespace

            test_shell.do_md_namespace_update(self.gc, args)

            mocked_update.assert_called_once_with('MyNamespace',
                                                  id='MyNamespace',
                                                  protected=True)
            utils.print_dict.assert_called_once_with(expect_namespace)

    def test_do_md_namespace_show(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'max_column_width': 80,
                                'resource_type': None})
        with mock.patch.object(self.gc.metadefs_namespace,
                               'get') as mocked_get:
            expect_namespace = {'namespace': 'MyNamespace'}

            mocked_get.return_value = expect_namespace

            test_shell.do_md_namespace_show(self.gc, args)

            mocked_get.assert_called_once_with('MyNamespace')
            utils.print_dict.assert_called_once_with(expect_namespace, 80)

    def test_do_md_namespace_show_resource_type(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'max_column_width': 80,
                                'resource_type': 'RESOURCE'})
        with mock.patch.object(self.gc.metadefs_namespace,
                               'get') as mocked_get:
            expect_namespace = {'namespace': 'MyNamespace'}

            mocked_get.return_value = expect_namespace

            test_shell.do_md_namespace_show(self.gc, args)

            mocked_get.assert_called_once_with('MyNamespace',
                                               resource_type='RESOURCE')
            utils.print_dict.assert_called_once_with(expect_namespace, 80)

    def test_do_md_namespace_list(self):
        args = self._make_args({'resource_type': None,
                                'visibility': None,
                                'page_size': None})
        with mock.patch.object(self.gc.metadefs_namespace,
                               'list') as mocked_list:
            expect_namespaces = [{'namespace': 'MyNamespace'}]

            mocked_list.return_value = expect_namespaces

            test_shell.do_md_namespace_list(self.gc, args)

            mocked_list.assert_called_once_with(filters={})
            utils.print_list.assert_called_once_with(expect_namespaces,
                                                     ['namespace'])

    def test_do_md_namespace_list_page_size(self):
        args = self._make_args({'resource_type': None,
                                'visibility': None,
                                'page_size': 2})
        with mock.patch.object(self.gc.metadefs_namespace,
                               'list') as mocked_list:
            expect_namespaces = [{'namespace': 'MyNamespace'}]

            mocked_list.return_value = expect_namespaces

            test_shell.do_md_namespace_list(self.gc, args)

            mocked_list.assert_called_once_with(filters={}, page_size=2)
            utils.print_list.assert_called_once_with(expect_namespaces,
                                                     ['namespace'])

    def test_do_md_namespace_list_one_filter(self):
        args = self._make_args({'resource_types': ['OS::Compute::Aggregate'],
                                'visibility': None,
                                'page_size': None})
        with mock.patch.object(self.gc.metadefs_namespace, 'list') as \
                mocked_list:
            expect_namespaces = [{'namespace': 'MyNamespace'}]

            mocked_list.return_value = expect_namespaces

            test_shell.do_md_namespace_list(self.gc, args)

            mocked_list.assert_called_once_with(filters={
                'resource_types': ['OS::Compute::Aggregate']})
            utils.print_list.assert_called_once_with(expect_namespaces,
                                                     ['namespace'])

    def test_do_md_namespace_list_all_filters(self):
        args = self._make_args({'resource_types': ['OS::Compute::Aggregate'],
                                'visibility': 'public',
                                'page_size': None})
        with mock.patch.object(self.gc.metadefs_namespace,
                               'list') as mocked_list:
            expect_namespaces = [{'namespace': 'MyNamespace'}]

            mocked_list.return_value = expect_namespaces

            test_shell.do_md_namespace_list(self.gc, args)

            mocked_list.assert_called_once_with(filters={
                'resource_types': ['OS::Compute::Aggregate'],
                'visibility': 'public'})
            utils.print_list.assert_called_once_with(expect_namespaces,
                                                     ['namespace'])

    def test_do_md_namespace_list_unknown_filter(self):
        args = self._make_args({'resource_type': None,
                                'visibility': None,
                                'some_arg': 'some_value',
                                'page_size': None})
        with mock.patch.object(self.gc.metadefs_namespace,
                               'list') as mocked_list:
            expect_namespaces = [{'namespace': 'MyNamespace'}]

            mocked_list.return_value = expect_namespaces

            test_shell.do_md_namespace_list(self.gc, args)

            mocked_list.assert_called_once_with(filters={})
            utils.print_list.assert_called_once_with(expect_namespaces,
                                                     ['namespace'])

    def test_do_md_namespace_delete(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'content': False})
        with mock.patch.object(self.gc.metadefs_namespace, 'delete') as \
                mocked_delete:
            test_shell.do_md_namespace_delete(self.gc, args)

            mocked_delete.assert_called_once_with('MyNamespace')

    def test_do_md_resource_type_associate(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'name': 'MyResourceType',
                                'prefix': 'PREFIX:'})
        with mock.patch.object(self.gc.metadefs_resource_type,
                               'associate') as mocked_associate:
            expect_rt = {
                'namespace': 'MyNamespace',
                'name': 'MyResourceType',
                'prefix': 'PREFIX:'
            }

            mocked_associate.return_value = expect_rt

            test_shell.do_md_resource_type_associate(self.gc, args)

            mocked_associate.assert_called_once_with('MyNamespace',
                                                     **expect_rt)
            utils.print_dict.assert_called_once_with(expect_rt)

    def test_do_md_resource_type_deassociate(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'resource_type': 'MyResourceType'})
        with mock.patch.object(self.gc.metadefs_resource_type,
                               'deassociate') as mocked_deassociate:
            test_shell.do_md_resource_type_deassociate(self.gc, args)

            mocked_deassociate.assert_called_once_with('MyNamespace',
                                                       'MyResourceType')

    def test_do_md_resource_type_list(self):
        args = self._make_args({})
        with mock.patch.object(self.gc.metadefs_resource_type,
                               'list') as mocked_list:
            expect_objects = ['MyResourceType1', 'MyResourceType2']

            mocked_list.return_value = expect_objects

            test_shell.do_md_resource_type_list(self.gc, args)

            self.assertEqual(1, mocked_list.call_count)

    def test_do_md_namespace_resource_type_list(self):
        args = self._make_args({'namespace': 'MyNamespace'})
        with mock.patch.object(self.gc.metadefs_resource_type,
                               'get') as mocked_get:
            expect_objects = [{'namespace': 'MyNamespace',
                               'object': 'MyObject'}]

            mocked_get.return_value = expect_objects

            test_shell.do_md_namespace_resource_type_list(self.gc, args)

            mocked_get.assert_called_once_with('MyNamespace')
            utils.print_list.assert_called_once_with(expect_objects,
                                                     ['name', 'prefix',
                                                      'properties_target'])

    def test_do_md_property_create(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'name': "MyProperty",
                                'title': "Title",
                                'schema': '{}'})
        with mock.patch.object(self.gc.metadefs_property,
                               'create') as mocked_create:
            expect_property = {
                'namespace': 'MyNamespace',
                'name': 'MyProperty',
                'title': 'Title'
            }

            mocked_create.return_value = expect_property

            test_shell.do_md_property_create(self.gc, args)

            mocked_create.assert_called_once_with('MyNamespace',
                                                  name='MyProperty',
                                                  title='Title')
            utils.print_dict.assert_called_once_with(expect_property)

    def test_do_md_property_create_invalid_schema(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'name': "MyProperty",
                                'title': "Title",
                                'schema': 'Invalid'})
        self.assertRaises(SystemExit, test_shell.do_md_property_create,
                          self.gc, args)

    def test_do_md_property_update(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'property': 'MyProperty',
                                'name': 'NewName',
                                'title': "Title",
                                'schema': '{}'})
        with mock.patch.object(self.gc.metadefs_property,
                               'update') as mocked_update:
            expect_property = {
                'namespace': 'MyNamespace',
                'name': 'MyProperty',
                'title': 'Title'
            }

            mocked_update.return_value = expect_property

            test_shell.do_md_property_update(self.gc, args)

            mocked_update.assert_called_once_with('MyNamespace', 'MyProperty',
                                                  name='NewName',
                                                  title='Title')
            utils.print_dict.assert_called_once_with(expect_property)

    def test_do_md_property_update_invalid_schema(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'property': 'MyProperty',
                                'name': "MyObject",
                                'title': "Title",
                                'schema': 'Invalid'})
        self.assertRaises(SystemExit, test_shell.do_md_property_update,
                          self.gc, args)

    def test_do_md_property_show(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'property': 'MyProperty',
                                'max_column_width': 80})
        with mock.patch.object(self.gc.metadefs_property, 'get') as mocked_get:
            expect_property = {
                'namespace': 'MyNamespace',
                'property': 'MyProperty',
                'title': 'Title'
            }

            mocked_get.return_value = expect_property

            test_shell.do_md_property_show(self.gc, args)

            mocked_get.assert_called_once_with('MyNamespace', 'MyProperty')
            utils.print_dict.assert_called_once_with(expect_property, 80)

    def test_do_md_property_delete(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'property': 'MyProperty'})
        with mock.patch.object(self.gc.metadefs_property,
                               'delete') as mocked_delete:
            test_shell.do_md_property_delete(self.gc, args)

            mocked_delete.assert_called_once_with('MyNamespace', 'MyProperty')

    def test_do_md_namespace_property_delete(self):
        args = self._make_args({'namespace': 'MyNamespace'})
        with mock.patch.object(self.gc.metadefs_property,
                               'delete_all') as mocked_delete_all:
            test_shell.do_md_namespace_properties_delete(self.gc, args)

            mocked_delete_all.assert_called_once_with('MyNamespace')

    def test_do_md_property_list(self):
        args = self._make_args({'namespace': 'MyNamespace'})
        with mock.patch.object(self.gc.metadefs_property,
                               'list') as mocked_list:
            expect_objects = [{'namespace': 'MyNamespace',
                               'property': 'MyProperty',
                               'title': 'MyTitle'}]

            mocked_list.return_value = expect_objects

            test_shell.do_md_property_list(self.gc, args)

            mocked_list.assert_called_once_with('MyNamespace')
            utils.print_list.assert_called_once_with(expect_objects,
                                                     ['name', 'title', 'type'])

    def test_do_md_object_create(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'name': "MyObject",
                                'schema': '{}'})
        with mock.patch.object(self.gc.metadefs_object,
                               'create') as mocked_create:
            expect_object = {
                'namespace': 'MyNamespace',
                'name': 'MyObject'
            }

            mocked_create.return_value = expect_object

            test_shell.do_md_object_create(self.gc, args)

            mocked_create.assert_called_once_with('MyNamespace',
                                                  name='MyObject')
            utils.print_dict.assert_called_once_with(expect_object)

    def test_do_md_object_create_invalid_schema(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'name': "MyObject",
                                'schema': 'Invalid'})
        self.assertRaises(SystemExit, test_shell.do_md_object_create,
                          self.gc, args)

    def test_do_md_object_update(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'object': 'MyObject',
                                'name': 'NewName',
                                'schema': '{}'})
        with mock.patch.object(self.gc.metadefs_object,
                               'update') as mocked_update:
            expect_object = {
                'namespace': 'MyNamespace',
                'name': 'MyObject'
            }

            mocked_update.return_value = expect_object

            test_shell.do_md_object_update(self.gc, args)

            mocked_update.assert_called_once_with('MyNamespace', 'MyObject',
                                                  name='NewName')
            utils.print_dict.assert_called_once_with(expect_object)

    def test_do_md_object_update_invalid_schema(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'object': 'MyObject',
                                'name': "MyObject",
                                'schema': 'Invalid'})
        self.assertRaises(SystemExit, test_shell.do_md_object_update,
                          self.gc, args)

    def test_do_md_object_show(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'object': 'MyObject',
                                'max_column_width': 80})
        with mock.patch.object(self.gc.metadefs_object, 'get') as mocked_get:
            expect_object = {
                'namespace': 'MyNamespace',
                'object': 'MyObject'
            }

            mocked_get.return_value = expect_object

            test_shell.do_md_object_show(self.gc, args)

            mocked_get.assert_called_once_with('MyNamespace', 'MyObject')
            utils.print_dict.assert_called_once_with(expect_object, 80)

    def test_do_md_object_property_show(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'object': 'MyObject',
                                'property': 'MyProperty',
                                'max_column_width': 80})
        with mock.patch.object(self.gc.metadefs_object, 'get') as mocked_get:
            expect_object = {'name': 'MyObject',
                             'properties': {
                                 'MyProperty': {'type': 'string'}
                             }}

            mocked_get.return_value = expect_object

            test_shell.do_md_object_property_show(self.gc, args)

            mocked_get.assert_called_once_with('MyNamespace', 'MyObject')
            utils.print_dict.assert_called_once_with({'type': 'string',
                                                      'name': 'MyProperty'},
                                                     80)

    def test_do_md_object_property_show_non_existing(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'object': 'MyObject',
                                'property': 'MyProperty',
                                'max_column_width': 80})
        with mock.patch.object(self.gc.metadefs_object, 'get') as mocked_get:
            expect_object = {'name': 'MyObject', 'properties': {}}
            mocked_get.return_value = expect_object

            self.assertRaises(SystemExit,
                              test_shell.do_md_object_property_show,
                              self.gc, args)
            mocked_get.assert_called_once_with('MyNamespace', 'MyObject')

    def test_do_md_object_delete(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'object': 'MyObject'})
        with mock.patch.object(self.gc.metadefs_object,
                               'delete') as mocked_delete:
            test_shell.do_md_object_delete(self.gc, args)

            mocked_delete.assert_called_once_with('MyNamespace', 'MyObject')

    def test_do_md_namespace_objects_delete(self):
        args = self._make_args({'namespace': 'MyNamespace'})
        with mock.patch.object(self.gc.metadefs_object,
                               'delete_all') as mocked_delete_all:
            test_shell.do_md_namespace_objects_delete(self.gc, args)

            mocked_delete_all.assert_called_once_with('MyNamespace')

    def test_do_md_object_list(self):
        args = self._make_args({'namespace': 'MyNamespace'})
        with mock.patch.object(self.gc.metadefs_object, 'list') as mocked_list:
            expect_objects = [{'namespace': 'MyNamespace',
                               'object': 'MyObject'}]

            mocked_list.return_value = expect_objects

            test_shell.do_md_object_list(self.gc, args)

            mocked_list.assert_called_once_with('MyNamespace')
            utils.print_list.assert_called_once_with(
                expect_objects,
                ['name', 'description'],
                field_settings={
                    'description': {'align': 'l', 'max_width': 50}})

    def test_do_md_tag_create(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'name': 'MyTag'})
        with mock.patch.object(self.gc.metadefs_tag,
                               'create') as mocked_create:
            expect_tag = {
                'namespace': 'MyNamespace',
                'name': 'MyTag'
            }

            mocked_create.return_value = expect_tag

            test_shell.do_md_tag_create(self.gc, args)

            mocked_create.assert_called_once_with('MyNamespace', 'MyTag')
            utils.print_dict.assert_called_once_with(expect_tag)

    def test_do_md_tag_update(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'tag': 'MyTag',
                                'name': 'NewTag'})
        with mock.patch.object(self.gc.metadefs_tag,
                               'update') as mocked_update:
            expect_tag = {
                'namespace': 'MyNamespace',
                'name': 'NewTag'
            }

            mocked_update.return_value = expect_tag

            test_shell.do_md_tag_update(self.gc, args)

            mocked_update.assert_called_once_with('MyNamespace', 'MyTag',
                                                  name='NewTag')
            utils.print_dict.assert_called_once_with(expect_tag)

    def test_do_md_tag_show(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'tag': 'MyTag',
                                'sort_dir': 'desc'})
        with mock.patch.object(self.gc.metadefs_tag, 'get') as mocked_get:
            expect_tag = {
                'namespace': 'MyNamespace',
                'tag': 'MyTag'
            }

            mocked_get.return_value = expect_tag

            test_shell.do_md_tag_show(self.gc, args)

            mocked_get.assert_called_once_with('MyNamespace', 'MyTag')
            utils.print_dict.assert_called_once_with(expect_tag)

    def test_do_md_tag_delete(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'tag': 'MyTag'})
        with mock.patch.object(self.gc.metadefs_tag,
                               'delete') as mocked_delete:
            test_shell.do_md_tag_delete(self.gc, args)

            mocked_delete.assert_called_once_with('MyNamespace', 'MyTag')

    def test_do_md_namespace_tags_delete(self):
        args = self._make_args({'namespace': 'MyNamespace'})
        with mock.patch.object(self.gc.metadefs_tag,
                               'delete_all') as mocked_delete_all:
            test_shell.do_md_namespace_tags_delete(self.gc, args)

            mocked_delete_all.assert_called_once_with('MyNamespace')

    def test_do_md_tag_list(self):
        args = self._make_args({'namespace': 'MyNamespace'})
        with mock.patch.object(self.gc.metadefs_tag, 'list') as mocked_list:
            expect_tags = [{'namespace': 'MyNamespace',
                            'tag': 'MyTag'}]

            mocked_list.return_value = expect_tags

            test_shell.do_md_tag_list(self.gc, args)

            mocked_list.assert_called_once_with('MyNamespace')
            utils.print_list.assert_called_once_with(
                expect_tags,
                ['name'],
                field_settings={
                    'description': {'align': 'l', 'max_width': 50}})

    def test_do_md_tag_create_multiple(self):
        args = self._make_args({'namespace': 'MyNamespace',
                                'delim': ',',
                                'names': 'MyTag1, MyTag2'})
        with mock.patch.object(
                self.gc.metadefs_tag, 'create_multiple') as mocked_create_tags:
            expect_tags = [{'tags': [{'name': 'MyTag1'}, {'name': 'MyTag2'}]}]

            mocked_create_tags.return_value = expect_tags

            test_shell.do_md_tag_create_multiple(self.gc, args)

            mocked_create_tags.assert_called_once_with(
                'MyNamespace', tags=['MyTag1', 'MyTag2'])
            utils.print_list.assert_called_once_with(
                expect_tags,
                ['name'],
                field_settings={
                    'description': {'align': 'l', 'max_width': 50}})
