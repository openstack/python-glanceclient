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
import os
import tempfile

import mock

from glanceclient import exc
from glanceclient import shell as openstack_shell

#NOTE (esheffield) Used for the schema caching tests
from glanceclient.v2 import schemas as schemas
import json

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
        # NOTE(guochbo): Can't compare ArgumentParser instances directly
        # Convert ArgumentPaser to string first.
        self.assertEqual(str(expected), str(actual_parser))

    def test_get_image_url_by_ipv6Addr_host(self):
        fake_args = lambda: None
        setattr(fake_args, 'os_image_url', None)
        setattr(fake_args, 'host', '2011:2013:1:f101::1')
        setattr(fake_args, 'use_ssl', True)
        setattr(fake_args, 'port', '9292')
        expected_image_url = 'https://[2011:2013:1:f101::1]:9292/'
        test_shell = openstack_shell.OpenStackImagesShell()
        targeted_image_url = test_shell._get_image_url(fake_args)
        self.assertEqual(expected_image_url, targeted_image_url)


class ShellCacheSchemaTest(utils.TestCase):
    def setUp(self):
        super(ShellCacheSchemaTest, self).setUp()
        self.shell = openstack_shell.OpenStackImagesShell()
        self._mock_client_setup()

    def _mock_client_setup(self):
        self.schema_dict = {
            'name': 'image',
            'properties': {
                'name': {'type': 'string', 'description': 'Name of image'},
            },
        }

        self.client = mock.Mock()
        self.client.schemas.get.return_value = schemas.Schema(self.schema_dict)

    def _make_args(self, args):
        class Args():
            def __init__(self, entries):
                self.__dict__.update(entries)

        return Args(args)

    def _write_file(self, path, text):
        with file(path, 'w') as f:
            f.write(text)

    def _read_file(self, path):
        with file(path, 'r') as f:
            text = f.read()

        return text

    def test_cache_schema_gets_when_not_exists(self):
        cache_dir = tempfile.gettempdir()

        cache_file = cache_dir + '/image_schema.json'

        if os.path.exists(cache_file):
            os.remove(cache_file)

        options = {
            'get_schema': False
        }

        with mock.patch.object(self.shell, '_get_versioned_client')\
                as mocked_get_client:
            mocked_get_client.return_value = self.client
            self.shell._cache_schema(self._make_args(options),
                                     home_dir=cache_dir)

        self.assertTrue(os.path.exists(cache_file))

    def test_cache_schema_gets_when_forced(self):
        cache_dir = tempfile.gettempdir()

        cache_file = cache_dir + '/image_schema.json'

        dummy_schema = 'my dummy schema'
        self._write_file(cache_file, dummy_schema)

        options = {
            'get_schema': True
        }

        with mock.patch.object(self.shell, '_get_versioned_client') \
                as mocked_get_client:
            mocked_get_client.return_value = self.client
            self.shell._cache_schema(self._make_args(options),
                                     home_dir=cache_dir)

        self.assertTrue(os.path.exists(cache_file))
        text = self._read_file(cache_file)
        self.assertEqual(text, json.dumps(self.schema_dict))

    def test_cache_schema_leaves_when_present_not_forced(self):
        cache_dir = tempfile.gettempdir()

        cache_file = cache_dir + '/image_schema.json'

        dummy_schema = 'my dummy schema'
        self._write_file(cache_file, dummy_schema)

        options = {
            'get_schema': False
        }

        with mock.patch.object(self.shell, '_get_versioned_client') \
                as mocked_get_client:
            mocked_get_client.return_value = self.client
            self.shell._cache_schema(self._make_args(options),
                                     home_dir=cache_dir)

        self.assertTrue(os.path.exists(cache_file))
        text = self._read_file(cache_file)
        self.assertEqual(text, dummy_schema)
