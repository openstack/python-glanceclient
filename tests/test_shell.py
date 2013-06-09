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

import argparse
import os

from glanceclient import exc
from glanceclient import shell as openstack_shell
from tests import utils

DEFAULT_IMAGE_URL = 'http://127.0.0.1:5000/'
DEFAULT_USERNAME = 'username'
DEFAULT_PASSWORD = 'password'
DEFAULT_TENANT_ID = 'tenant_id'
DEFAULT_TENANT_NAME = 'tenant_name'
DEFAULT_AUTH_URL = 'http://127.0.0.1:5000/v2.0/'
DEFAULT_AUTH_TOKEN = ' 3bcc3d3a03f44e3d8377f9247b0ad155'
TEST_SERVICE_URL = 'http://127.0.0.1:5000/'


class ShellTest(utils.TestCase):
    def setUp(self):
        super(ShellTest, self).setUp()
        global _old_env
        fake_env = {
            'OS_USERNAME': DEFAULT_USERNAME,
            'OS_PASSWORD': DEFAULT_PASSWORD,
            'OS_TENANT_NAME': DEFAULT_TENANT_NAME,
            'OS_AUTH_URL': DEFAULT_AUTH_URL,
            'OS_IMAGE_URL': DEFAULT_IMAGE_URL,
            'OS_AUTH_TOKEN': DEFAULT_AUTH_TOKEN}
        _old_env, os.environ = os.environ, fake_env.copy()

        global shell, _shell, assert_called, assert_called_anytime
        _shell = openstack_shell.OpenStackImagesShell()
        shell = lambda cmd: _shell.main(cmd.split())

    def tearDown(self):
        super(ShellTest, self).tearDown()
        global _old_env
        os.environ = _old_env

    def test_help_unknown_command(self):
        shell = openstack_shell.OpenStackImagesShell()
        argstr = 'help foofoo'
        self.assertRaises(exc.CommandError, shell.main, argstr.split())

    def test_help(self):
        shell = openstack_shell.OpenStackImagesShell()
        argstr = 'help'
        actual = shell.main(argstr.split())
        self.assertEqual(0, actual)

    def test_help_on_subcommand_error(self):
        self.assertRaises(exc.CommandError, shell, 'help bad')

    def test_get_base_parser(self):
        test_shell = openstack_shell.OpenStackImagesShell()
        actual_parser = test_shell.get_base_parser()
        description = 'Command-line interface to the OpenStack Images API.'
        expected = argparse.ArgumentParser(
            prog='glance', usage=None,
            description=description,
            version=None,
            conflict_handler='error',
            add_help=False,
            formatter_class=openstack_shell.HelpFormatter,)
        self.assertTrue(expected, actual_parser)
