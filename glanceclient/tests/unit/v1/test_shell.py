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
import json
import os
import six
import subprocess
import tempfile
import testtools

import mock

from glanceclient import exc
from glanceclient import shell

import glanceclient.v1.client as client
import glanceclient.v1.images
import glanceclient.v1.shell as v1shell

from glanceclient.tests import utils

if six.PY3:
    import io
    file_type = io.IOBase
else:
    file_type = file

fixtures = {
    '/v1/images/96d2c7e1-de4e-4612-8aa2-ba26610c804e': {
        'PUT': (
            {
                'Location': 'http://fakeaddress.com:9292/v1/images/'
                            '96d2c7e1-de4e-4612-8aa2-ba26610c804e',
                'Etag': 'f8a2eeee2dc65b3d9b6e63678955bd83',
                'X-Openstack-Request-Id':
                        'req-b645039d-e1c7-43e5-b27b-2d18a173c42b',
                'Date': 'Mon, 29 Apr 2013 10:24:32 GMT'
            },
            json.dumps({
                'image': {
                    'status': 'active', 'name': 'testimagerename',
                    'deleted': False,
                    'container_format': 'ami',
                    'created_at': '2013-04-25T15:47:43',
                    'disk_format': 'ami',
                    'updated_at': '2013-04-29T10:24:32',
                    'id': '96d2c7e1-de4e-4612-8aa2-ba26610c804e',
                    'min_disk': 0,
                    'protected': False,
                    'min_ram': 0,
                    'checksum': 'f8a2eeee2dc65b3d9b6e63678955bd83',
                    'owner': '1310db0cce8f40b0987a5acbe139765a',
                    'is_public': True,
                    'deleted_at': None,
                    'properties': {
                        'kernel_id': '1b108400-65d8-4762-9ea4-1bf6c7be7568',
                        'ramdisk_id': 'b759bee9-0669-4394-a05c-fa2529b1c114'
                    },
                    'size': 25165824
                }
            })
        ),
        'HEAD': (
            {
                'x-image-meta-id': '96d2c7e1-de4e-4612-8aa2-ba26610c804e',
                'x-image-meta-status': 'active'
            },
            None
        ),
        'GET': (
            {
                'x-image-meta-status': 'active',
                'x-image-meta-owner': '1310db0cce8f40b0987a5acbe139765a',
                'x-image-meta-name': 'cirros-0.3.1-x86_64-uec',
                'x-image-meta-container_format': 'ami',
                'x-image-meta-created_at': '2013-04-25T15:47:43',
                'etag': 'f8a2eeee2dc65b3d9b6e63678955bd83',
                'location': 'http://fakeaddress.com:9292/v1/images/'
                            '96d2c7e1-de4e-4612-8aa2-ba26610c804e',
                'x-image-meta-min_ram': '0',
                'x-image-meta-updated_at': '2013-04-25T15:47:43',
                'x-image-meta-id': '96d2c7e1-de4e-4612-8aa2-ba26610c804e',
                'x-image-meta-property-ramdisk_id':
                        'b759bee9-0669-4394-a05c-fa2529b1c114',
                'date': 'Mon, 29 Apr 2013 09:25:17 GMT',
                'x-image-meta-property-kernel_id':
                        '1b108400-65d8-4762-9ea4-1bf6c7be7568',
                'x-openstack-request-id':
                        'req-842735bf-77e8-44a7-bfd1-7d95c52cec7f',
                'x-image-meta-deleted': 'False',
                'x-image-meta-checksum': 'f8a2eeee2dc65b3d9b6e63678955bd83',
                'x-image-meta-protected': 'False',
                'x-image-meta-min_disk': '0',
                'x-image-meta-size': '25165824',
                'x-image-meta-is_public': 'True',
                'content-type': 'text/html; charset=UTF-8',
                'x-image-meta-disk_format': 'ami',
            },
            None
        )
    },
    '/v1/images/44d2c7e1-de4e-4612-8aa2-ba26610c444f': {
        'PUT': (
            {
                'Location': 'http://fakeaddress.com:9292/v1/images/'
                            '44d2c7e1-de4e-4612-8aa2-ba26610c444f',
                'Etag': 'f8a2eeee2dc65b3d9b6e63678955bd83',
                'X-Openstack-Request-Id':
                        'req-b645039d-e1c7-43e5-b27b-2d18a173c42b',
                'Date': 'Mon, 29 Apr 2013 10:24:32 GMT'
            },
            json.dumps({
                'image': {
                    'status': 'queued', 'name': 'testimagerename',
                    'deleted': False,
                    'container_format': 'ami',
                    'created_at': '2013-04-25T15:47:43',
                    'disk_format': 'ami',
                    'updated_at': '2013-04-29T10:24:32',
                    'id': '44d2c7e1-de4e-4612-8aa2-ba26610c444f',
                    'min_disk': 0,
                    'protected': False,
                    'min_ram': 0,
                    'checksum': 'f8a2eeee2dc65b3d9b6e63678955bd83',
                    'owner': '1310db0cce8f40b0987a5acbe139765a',
                    'is_public': True,
                    'deleted_at': None,
                    'properties': {
                        'kernel_id':
                                '1b108400-65d8-4762-9ea4-1bf6c7be7568',
                        'ramdisk_id':
                                'b759bee9-0669-4394-a05c-fa2529b1c114'
                    },
                    'size': 25165824
                }
            })
        ),
        'HEAD': (
            {
                'x-image-meta-id': '44d2c7e1-de4e-4612-8aa2-ba26610c444f',
                'x-image-meta-status': 'queued'
            },
            None
        ),
        'GET': (
            {
                'x-image-meta-status': 'queued',
                'x-image-meta-owner': '1310db0cce8f40b0987a5acbe139765a',
                'x-image-meta-name': 'cirros-0.3.1-x86_64-uec',
                'x-image-meta-container_format': 'ami',
                'x-image-meta-created_at': '2013-04-25T15:47:43',
                'etag': 'f8a2eeee2dc65b3d9b6e63678955bd83',
                'location': 'http://fakeaddress.com:9292/v1/images/'
                            '44d2c7e1-de4e-4612-8aa2-ba26610c444f',
                'x-image-meta-min_ram': '0',
                'x-image-meta-updated_at': '2013-04-25T15:47:43',
                'x-image-meta-id': '44d2c7e1-de4e-4612-8aa2-ba26610c444f',
                'x-image-meta-property-ramdisk_id':
                        'b759bee9-0669-4394-a05c-fa2529b1c114',
                'date': 'Mon, 29 Apr 2013 09:25:17 GMT',
                'x-image-meta-property-kernel_id':
                        '1b108400-65d8-4762-9ea4-1bf6c7be7568',
                'x-openstack-request-id':
                        'req-842735bf-77e8-44a7-bfd1-7d95c52cec7f',
                'x-image-meta-deleted': 'False',
                'x-image-meta-checksum': 'f8a2eeee2dc65b3d9b6e63678955bd83',
                'x-image-meta-protected': 'False',
                'x-image-meta-min_disk': '0',
                'x-image-meta-size': '25165824',
                'x-image-meta-is_public': 'True',
                'content-type': 'text/html; charset=UTF-8',
                'x-image-meta-disk_format': 'ami',
            },
            None
        )
    },
    '/v1/images/detail?limit=20&name=70aa106f-3750-4d7c-a5ce-0a535ac08d0a': {
        'GET': (
            {},
            {'images': [
                {
                    'id': '70aa106f-3750-4d7c-a5ce-0a535ac08d0a',
                    'name': 'imagedeleted',
                    'deleted': True,
                    'status': 'deleted',
                },
            ]},
        ),
    },
    '/v1/images/70aa106f-3750-4d7c-a5ce-0a535ac08d0a': {
        'HEAD': (
            {
                'x-image-meta-id': '70aa106f-3750-4d7c-a5ce-0a535ac08d0a',
                'x-image-meta-status': 'deleted'
            },
            None
        )
    }
}


class ShellInvalidEndpointandParameterTest(utils.TestCase):

    # Patch os.environ to avoid required auth info.
    def setUp(self):
        """Run before each test."""
        super(ShellInvalidEndpointandParameterTest, self).setUp()
        self.old_environment = os.environ.copy()
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

        self.gc = self._mock_glance_client()

    def _make_args(self, args):
        # NOTE(venkatesh): this conversion from a dict to an object
        # is required because the test_shell.do_xxx(gc, args) methods
        # expects the args to be attributes of an object. If passed as
        # dict directly, it throws an AttributeError.
        class Args(object):
            def __init__(self, entries):
                self.__dict__.update(entries)

        return Args(args)

    def _mock_glance_client(self):
        my_mocked_gc = mock.Mock()
        my_mocked_gc.get.return_value = {}
        return my_mocked_gc

    def tearDown(self):
        super(ShellInvalidEndpointandParameterTest, self).tearDown()
        os.environ = self.old_environment
        self.patched.stop()

    def run_command(self, cmd):
        self.shell.main(cmd.split())

    def assert_called(self, method, url, body=None, **kwargs):
        return self.shell.cs.assert_called(method, url, body, **kwargs)

    def assert_called_anytime(self, method, url, body=None):
        return self.shell.cs.assert_called_anytime(method, url, body)

    def test_image_list_invalid_endpoint(self):
        self.assertRaises(
            exc.CommunicationError, self.run_command, 'image-list')

    def test_image_create_invalid_endpoint(self):
        self.assertRaises(
            exc.CommunicationError,
            self.run_command, 'image-create')

    def test_image_delete_invalid_endpoint(self):
        self.assertRaises(
            exc.CommunicationError,
            self.run_command, 'image-delete <fake>')

    def test_image_download_invalid_endpoint(self):
        self.assertRaises(
            exc.CommunicationError,
            self.run_command, 'image-download <fake>')

    def test_members_list_invalid_endpoint(self):
        self.assertRaises(
            exc.CommunicationError,
            self.run_command, 'member-list --image-id fake')

    def test_image_show_invalid_endpoint(self):
        self.assertRaises(
            exc.CommunicationError,
            self.run_command, 'image-show --human-readable <IMAGE_ID>')

    def test_member_create_invalid_endpoint(self):
        self.assertRaises(
            exc.CommunicationError,
            self.run_command,
            'member-create --can-share <IMAGE_ID> <TENANT_ID>')

    def test_member_delete_invalid_endpoint(self):
        self.assertRaises(
            exc.CommunicationError,
            self.run_command,
            'member-delete  <IMAGE_ID> <TENANT_ID>')

    @mock.patch('sys.stderr')
    def test_image_create_invalid_size_parameter(self, __):
        self.assertRaises(
            SystemExit,
            self.run_command, 'image-create --size 10gb')

    @mock.patch('sys.stderr')
    def test_image_create_invalid_ram_parameter(self, __):
        self.assertRaises(
            SystemExit,
            self.run_command, 'image-create --min-ram 10gb')

    @mock.patch('sys.stderr')
    def test_image_create_invalid_min_disk_parameter(self, __):
        self.assertRaises(
            SystemExit,
            self.run_command, 'image-create --min-disk 10gb')

    @mock.patch('sys.stderr')
    def test_image_create_missing_disk_format(self, __):
        # We test for all possible sources
        for origin in ('--file', '--location', '--copy-from'):
            e = self.assertRaises(exc.CommandError, self.run_command,
                                  '--os-image-api-version 1 image-create ' +
                                  origin + ' fake_src --container-format bare')
            self.assertEqual('error: Must provide --disk-format when using '
                             + origin + '.', e.message)

    @mock.patch('sys.stderr')
    def test_image_create_missing_container_format(self, __):
        # We test for all possible sources
        for origin in ('--file', '--location', '--copy-from'):
            e = self.assertRaises(exc.CommandError, self.run_command,
                                  '--os-image-api-version 1 image-create ' +
                                  origin + ' fake_src --disk-format qcow2')
            self.assertEqual('error: Must provide --container-format when '
                             'using ' + origin + '.', e.message)

    @mock.patch('sys.stderr')
    def test_image_create_missing_container_format_stdin_data(self, __):
        # Fake that get_data_file method returns data
        self.mock_get_data_file.return_value = six.StringIO()
        e = self.assertRaises(exc.CommandError, self.run_command,
                              '--os-image-api-version 1 image-create'
                              ' --disk-format qcow2')
        self.assertEqual('error: Must provide --container-format when '
                         'using stdin.', e.message)

    @mock.patch('sys.stderr')
    def test_image_create_missing_disk_format_stdin_data(self, __):
        # Fake that get_data_file method returns data
        self.mock_get_data_file.return_value = six.StringIO()
        e = self.assertRaises(exc.CommandError, self.run_command,
                              '--os-image-api-version 1 image-create'
                              ' --container-format bare')
        self.assertEqual('error: Must provide --disk-format when using stdin.',
                         e.message)

    @mock.patch('sys.stderr')
    def test_image_update_invalid_size_parameter(self, __):
        self.assertRaises(
            SystemExit,
            self.run_command, 'image-update --size 10gb')

    @mock.patch('sys.stderr')
    def test_image_update_invalid_min_disk_parameter(self, __):
        self.assertRaises(
            SystemExit,
            self.run_command, 'image-update --min-disk 10gb')

    @mock.patch('sys.stderr')
    def test_image_update_invalid_ram_parameter(self, __):
        self.assertRaises(
            SystemExit,
            self.run_command, 'image-update --min-ram 10gb')

    @mock.patch('sys.stderr')
    def test_image_list_invalid_min_size_parameter(self, __):
        self.assertRaises(
            SystemExit,
            self.run_command, 'image-list --size-min 10gb')

    @mock.patch('sys.stderr')
    def test_image_list_invalid_max_size_parameter(self, __):
        self.assertRaises(
            SystemExit,
            self.run_command, 'image-list --size-max 10gb')

    def test_do_image_list_with_changes_since(self):
        input = {
            'name': None,
            'limit': None,
            'status': None,
            'container_format': 'bare',
            'size_min': None,
            'size_max': None,
            'is_public': True,
            'disk_format': 'raw',
            'page_size': 20,
            'visibility': True,
            'member_status': 'Fake',
            'owner': 'test',
            'checksum': 'fake_checksum',
            'tag': 'fake tag',
            'properties': [],
            'sort_key': None,
            'sort_dir': None,
            'all_tenants': False,
            'human_readable': True,
            'changes_since': '2011-1-1'
        }
        args = self._make_args(input)
        with mock.patch.object(self.gc.images, 'list') as mocked_list:
            mocked_list.return_value = {}

            v1shell.do_image_list(self.gc, args)

            exp_img_filters = {'container_format': 'bare',
                               'changes-since': '2011-1-1',
                               'disk_format': 'raw',
                               'is_public': True}
            mocked_list.assert_called_once_with(sort_dir=None,
                                                sort_key=None,
                                                owner='test',
                                                page_size=20,
                                                filters=exp_img_filters)


class ShellStdinHandlingTests(testtools.TestCase):

    def _fake_update_func(self, *args, **kwargs):
        """Replace glanceclient.images.update with a fake.

        To determine the parameters that would be supplied with the update
        request.
        """

        # Store passed in args
        self.collected_args = (args, kwargs)

        # Return the first arg, which is an image,
        # as do_image_update expects this.
        return args[0]

    def setUp(self):
        super(ShellStdinHandlingTests, self).setUp()
        self.api = utils.FakeAPI(fixtures)
        self.gc = client.Client("http://fakeaddress.com")
        self.gc.images = glanceclient.v1.images.ImageManager(self.api)

        # Store real stdin, so it can be restored in tearDown.
        self.real_sys_stdin_fd = os.dup(0)

        # Replace stdin with a FD that points to /dev/null.
        dev_null = open('/dev/null')
        self.dev_null_fd = dev_null.fileno()
        os.dup2(dev_null.fileno(), 0)

        # Replace the image update function with a fake,
        # so that we can tell if the data field was set correctly.
        self.real_update_func = self.gc.images.update
        self.collected_args = []
        self.gc.images.update = self._fake_update_func

    def tearDown(self):
        """Restore stdin and gc.images.update to their pretest states."""
        super(ShellStdinHandlingTests, self).tearDown()

        def try_close(fd):
            try:
                os.close(fd)
            except OSError:
                # Already closed
                pass

        # Restore stdin
        os.dup2(self.real_sys_stdin_fd, 0)

        # Close duplicate stdin handle
        try_close(self.real_sys_stdin_fd)

        # Close /dev/null handle
        try_close(self.dev_null_fd)

        # Restore the real image update function
        self.gc.images.update = self.real_update_func

    def _do_update(self, image='96d2c7e1-de4e-4612-8aa2-ba26610c804e'):
        """call v1/shell's do_image_update function."""

        v1shell.do_image_update(
            self.gc, argparse.Namespace(
                image=image,
                name='testimagerename',
                property={},
                purge_props=False,
                human_readable=False,
                file=None,
                progress=False
            )
        )

    def test_image_delete_deleted(self):
        self.assertRaises(
            exc.CommandError,
            v1shell.do_image_delete,
            self.gc,
            argparse.Namespace(
                images=['70aa106f-3750-4d7c-a5ce-0a535ac08d0a']
            )
        )

    def test_image_update_closed_stdin(self):
        """Test image update with a closed stdin.

        Supply glanceclient with a closed stdin, and perform an image
        update to an active image. Glanceclient should not attempt to read
        stdin.
        """

        # NOTE(hughsaunders) Close stdin, which is repointed to /dev/null by
        # setUp()
        os.close(0)

        self._do_update()

        self.assertTrue(
            'data' not in self.collected_args[1]
            or self.collected_args[1]['data'] is None
        )

    def test_image_update_opened_stdin(self):
        """Test image update with an opened stdin.

        Supply glanceclient with a stdin, and perform an image
        update to an active image. Glanceclient should not allow it.
        """

        self.assertRaises(
            SystemExit,
            v1shell.do_image_update,
            self.gc,
            argparse.Namespace(
                image='96d2c7e1-de4e-4612-8aa2-ba26610c804e',
                property={},
            )
        )

    def test_image_update_data_is_read_from_file(self):
        """Ensure that data is read from a file."""

        try:

            # NOTE(hughsaunders) Create a tmpfile, write some data to it and
            # set it as stdin
            f = open(tempfile.mktemp(), 'w+')
            f.write('Some Data')
            f.flush()
            f.seek(0)
            os.dup2(f.fileno(), 0)

            self._do_update('44d2c7e1-de4e-4612-8aa2-ba26610c444f')

            self.assertIn('data', self.collected_args[1])
            self.assertIsInstance(self.collected_args[1]['data'], file_type)
            self.assertEqual(b'Some Data',
                             self.collected_args[1]['data'].read())

        finally:
            try:
                f.close()
                os.remove(f.name)
            except Exception:
                pass

    def test_image_update_data_is_read_from_pipe(self):
        """Ensure that data is read from a pipe."""

        try:

            # NOTE(hughsaunders): Setup a pipe, duplicate it to stdin
            # ensure it is read.
            process = subprocess.Popen(['/bin/echo', 'Some Data'],
                                       stdout=subprocess.PIPE)
            os.dup2(process.stdout.fileno(), 0)

            self._do_update('44d2c7e1-de4e-4612-8aa2-ba26610c444f')

            self.assertIn('data', self.collected_args[1])
            self.assertIsInstance(self.collected_args[1]['data'], file_type)
            self.assertEqual(b'Some Data\n',
                             self.collected_args[1]['data'].read())

        finally:
            try:
                process.stdout.close()
            except OSError:
                pass
