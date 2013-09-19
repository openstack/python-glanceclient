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

import argparse
import json
import os
import subprocess
import tempfile
import testtools

from glanceclient import exc
from glanceclient import shell

import glanceclient.v1.client as client
import glanceclient.v1.images
import glanceclient.v1.shell as v1shell

from tests import utils

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
    }
}


class ShellInvalidEndpointTest(utils.TestCase):

    # Patch os.environ to avoid required auth info.
    def setUp(self):
        """Run before each test."""
        super(ShellInvalidEndpointTest, self).setUp()
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

    def tearDown(self):
        super(ShellInvalidEndpointTest, self).tearDown()
        os.environ = self.old_environment

    def run_command(self, cmd):
        self.shell.main(cmd.split())

    def assert_called(self, method, url, body=None, **kwargs):
        return self.shell.cs.assert_called(method, url, body, **kwargs)

    def assert_called_anytime(self, method, url, body=None):
        return self.shell.cs.assert_called_anytime(method, url, body)

    def test_image_list_invalid_endpoint(self):
        self.assertRaises(
            exc.InvalidEndpoint, self.run_command, 'image-list')

    def test_image_details_invalid_endpoint_legacy(self):
        self.assertRaises(
            exc.InvalidEndpoint, self.run_command, 'details')

    def test_image_update_invalid_endpoint_legacy(self):
        self.assertRaises(
            exc.InvalidEndpoint,
            self.run_command, 'update {"name":""test}')

    def test_image_index_invalid_endpoint_legacy(self):
        self.assertRaises(
            exc.InvalidEndpoint,
            self.run_command, 'index')

    def test_image_create_invalid_endpoint(self):
        self.assertRaises(
            exc.InvalidEndpoint,
            self.run_command, 'image-create')

    def test_image_delete_invalid_endpoint(self):
        self.assertRaises(
            exc.InvalidEndpoint,
            self.run_command, 'image-delete <fake>')

    def test_image_download_invalid_endpoint(self):
        self.assertRaises(
            exc.InvalidEndpoint,
            self.run_command, 'image-download <fake>')

    def test_image_members_invalid_endpoint(self):
        self.assertRaises(
            exc.InvalidEndpoint,
            self.run_command, 'image-members fake_id')

    def test_members_list_invalid_endpoint(self):
        self.assertRaises(
            exc.InvalidEndpoint,
            self.run_command, 'member-list --image-id fake')

    def test_member_replace_invalid_endpoint(self):
        self.assertRaises(
            exc.InvalidEndpoint,
            self.run_command, 'members-replace image_id member_id')

    def test_image_show_invalid_endpoint_legacy(self):
        self.assertRaises(
            exc.InvalidEndpoint, self.run_command, 'show image')

    def test_image_show_invalid_endpoint(self):
        self.assertRaises(
            exc.InvalidEndpoint,
            self.run_command, 'image-show --human-readable <IMAGE_ID>')

    def test_member_images_invalid_endpoint_legacy(self):
        self.assertRaises(
            exc.InvalidEndpoint,
            self.run_command, 'member-images member_id')

    def test_member_create_invalid_endpoint(self):
        self.assertRaises(
            exc.InvalidEndpoint,
            self.run_command,
            'member-create --can-share <IMAGE_ID> <TENANT_ID>')

    def test_member_delete_invalid_endpoint(self):
        self.assertRaises(
            exc.InvalidEndpoint,
            self.run_command,
            'member-delete  <IMAGE_ID> <TENANT_ID>')

    def test_member_add_invalid_endpoint(self):
        self.assertRaises(
            exc.InvalidEndpoint,
            self.run_command,
            'member-add  <IMAGE_ID> <TENANT_ID>')


class ShellStdinHandlingTests(testtools.TestCase):

    def _fake_update_func(self, *args, **kwargs):
        '''Function to replace glanceclient.images.update,
        to determine the parameters that would be supplied with the update
        request
        '''

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

    def test_image_update_closed_stdin(self):
        """Supply glanceclient with a closed stdin, and perform an image
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

            self.assertTrue('data' in self.collected_args[1])
            self.assertIsInstance(self.collected_args[1]['data'], file)
            self.assertEqual(self.collected_args[1]['data'].read(),
                             'Some Data')

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

            self.assertTrue('data' in self.collected_args[1])
            self.assertIsInstance(self.collected_args[1]['data'], file)
            self.assertEqual(self.collected_args[1]['data'].read(),
                             'Some Data\n')

        finally:
            try:
                process.stdout.close()
            except OSError:
                pass
