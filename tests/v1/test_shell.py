# Copyright 2013 OpenStack LLC.
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

import os

from glanceclient import exc
from glanceclient import shell
from tests import utils


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
            'OS_IMAGE_URL': 'http://no.where'}

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
