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
import os
import sys
import uuid

import fixtures
from keystoneclient import exceptions as ks_exc
from keystoneclient import fixture as ks_fixture
import mock
import requests
from requests_mock.contrib import fixture as rm_fixture
import six

from glanceclient.common import utils
from glanceclient import exc
from glanceclient import shell as openstack_shell
from glanceclient.tests import utils as testutils

#NOTE (esheffield) Used for the schema caching tests
from glanceclient.v2 import schemas as schemas
import json


DEFAULT_IMAGE_URL = 'http://127.0.0.1:5000/'
DEFAULT_USERNAME = 'username'
DEFAULT_PASSWORD = 'password'
DEFAULT_TENANT_ID = 'tenant_id'
DEFAULT_TENANT_NAME = 'tenant_name'
DEFAULT_PROJECT_ID = '0123456789'
DEFAULT_USER_DOMAIN_NAME = 'user_domain_name'
DEFAULT_UNVERSIONED_AUTH_URL = 'http://127.0.0.1:5000/'
DEFAULT_V2_AUTH_URL = '%sv2.0' % DEFAULT_UNVERSIONED_AUTH_URL
DEFAULT_V3_AUTH_URL = '%sv3' % DEFAULT_UNVERSIONED_AUTH_URL
DEFAULT_AUTH_TOKEN = ' 3bcc3d3a03f44e3d8377f9247b0ad155'
TEST_SERVICE_URL = 'http://127.0.0.1:5000/'

FAKE_V2_ENV = {'OS_USERNAME': DEFAULT_USERNAME,
               'OS_PASSWORD': DEFAULT_PASSWORD,
               'OS_TENANT_NAME': DEFAULT_TENANT_NAME,
               'OS_AUTH_URL': DEFAULT_V2_AUTH_URL,
               'OS_IMAGE_URL': DEFAULT_IMAGE_URL}

FAKE_V3_ENV = {'OS_USERNAME': DEFAULT_USERNAME,
               'OS_PASSWORD': DEFAULT_PASSWORD,
               'OS_PROJECT_ID': DEFAULT_PROJECT_ID,
               'OS_USER_DOMAIN_NAME': DEFAULT_USER_DOMAIN_NAME,
               'OS_AUTH_URL': DEFAULT_V3_AUTH_URL,
               'OS_IMAGE_URL': DEFAULT_IMAGE_URL}

TOKEN_ID = uuid.uuid4().hex

V2_TOKEN = ks_fixture.V2Token(token_id=TOKEN_ID)
V2_TOKEN.set_scope()
_s = V2_TOKEN.add_service('image', name='glance')
_s.add_endpoint(DEFAULT_IMAGE_URL)

V3_TOKEN = ks_fixture.V3Token()
V3_TOKEN.set_project_scope()
_s = V3_TOKEN.add_service('image', name='glance')
_s.add_standard_endpoints(public=DEFAULT_IMAGE_URL)


class ShellTest(testutils.TestCase):
    # auth environment to use
    auth_env = FAKE_V2_ENV.copy()
    # expected auth plugin to invoke
    token_url = DEFAULT_V2_AUTH_URL + '/tokens'

    # Patch os.environ to avoid required auth info
    def make_env(self, exclude=None):
        env = dict((k, v) for k, v in self.auth_env.items() if k != exclude)
        self.useFixture(fixtures.MonkeyPatch('os.environ', env))

    def setUp(self):
        super(ShellTest, self).setUp()
        global _old_env
        _old_env, os.environ = os.environ, self.auth_env

        self.requests = self.useFixture(rm_fixture.Fixture())

        json_list = ks_fixture.DiscoveryList(DEFAULT_UNVERSIONED_AUTH_URL)
        self.requests.get(DEFAULT_IMAGE_URL, json=json_list, status_code=300)

        json_v2 = {'version': ks_fixture.V2Discovery(DEFAULT_V2_AUTH_URL)}
        self.requests.get(DEFAULT_V2_AUTH_URL, json=json_v2)

        json_v3 = {'version': ks_fixture.V3Discovery(DEFAULT_V3_AUTH_URL)}
        self.requests.get(DEFAULT_V3_AUTH_URL, json=json_v3)

        self.v2_auth = self.requests.post(DEFAULT_V2_AUTH_URL + '/tokens',
                                          json=V2_TOKEN)

        headers = {'X-Subject-Token': TOKEN_ID}
        self.v3_auth = self.requests.post(DEFAULT_V3_AUTH_URL + '/auth/tokens',
                                          headers=headers,
                                          json=V3_TOKEN)

        global shell, _shell, assert_called, assert_called_anytime
        _shell = openstack_shell.OpenStackImagesShell()
        shell = lambda cmd: _shell.main(cmd.split())

    def tearDown(self):
        super(ShellTest, self).tearDown()
        global _old_env
        os.environ = _old_env

    def shell(self, argstr, exitcodes=(0,)):
        orig = sys.stdout
        orig_stderr = sys.stderr
        try:
            sys.stdout = six.StringIO()
            sys.stderr = six.StringIO()
            _shell = openstack_shell.OpenStackImagesShell()
            _shell.main(argstr.split())
        except SystemExit:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.assertIn(exc_value.code, exitcodes)
        finally:
            stdout = sys.stdout.getvalue()
            sys.stdout.close()
            sys.stdout = orig
            stderr = sys.stderr.getvalue()
            sys.stderr.close()
            sys.stderr = orig_stderr
        return (stdout, stderr)

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
            conflict_handler='error',
            add_help=False,
            formatter_class=openstack_shell.HelpFormatter,)
        # NOTE(guochbo): Can't compare ArgumentParser instances directly
        # Convert ArgumentPaser to string first.
        self.assertEqual(str(expected), str(actual_parser))

    @mock.patch.object(openstack_shell.OpenStackImagesShell,
                       '_get_versioned_client')
    def test_cert_and_key_args_interchangeable(self,
                                               mock_versioned_client):
        # make sure --os-cert and --os-key are passed correctly
        args = '--os-cert mycert --os-key mykey image-list'
        shell(args)
        assert mock_versioned_client.called
        ((api_version, args), kwargs) = mock_versioned_client.call_args
        self.assertEqual('mycert', args.os_cert)
        self.assertEqual('mykey', args.os_key)

        # make sure we get the same thing with --cert-file and --key-file
        args = '--cert-file mycertfile --key-file mykeyfile image-list'
        glance_shell = openstack_shell.OpenStackImagesShell()
        glance_shell.main(args.split())
        assert mock_versioned_client.called
        ((api_version, args), kwargs) = mock_versioned_client.call_args
        self.assertEqual('mycertfile', args.os_cert)
        self.assertEqual('mykeyfile', args.os_key)

    @mock.patch('glanceclient.v1.client.Client')
    def test_no_auth_with_token_and_image_url_with_v1(self, v1_client):
        # test no authentication is required if both token and endpoint url
        # are specified
        args = ('--os-auth-token mytoken --os-image-url https://image:1234/v1 '
                'image-list')
        glance_shell = openstack_shell.OpenStackImagesShell()
        glance_shell.main(args.split())
        assert v1_client.called
        (args, kwargs) = v1_client.call_args
        self.assertEqual('mytoken', kwargs['token'])
        self.assertEqual('https://image:1234', args[0])

    @mock.patch.object(openstack_shell.OpenStackImagesShell, '_cache_schemas')
    def test_no_auth_with_token_and_image_url_with_v2(self,
                                                      cache_schemas):
        with mock.patch('glanceclient.v2.client.Client') as v2_client:
            # test no authentication is required if both token and endpoint url
            # are specified
            args = ('--os-auth-token mytoken '
                    '--os-image-url https://image:1234/v2 '
                    '--os-image-api-version 2 image-list')
            glance_shell = openstack_shell.OpenStackImagesShell()
            glance_shell.main(args.split())
            ((args), kwargs) = v2_client.call_args
            self.assertEqual('https://image:1234', args[0])
            self.assertEqual('mytoken', kwargs['token'])

    def _assert_auth_plugin_args(self):
        # make sure our auth plugin is invoked with the correct args
        self.assertEqual(1, self.v2_auth.call_count)
        self.assertFalse(self.v3_auth.called)

        body = json.loads(self.v2_auth.last_request.body)

        self.assertEqual(self.auth_env['OS_TENANT_NAME'],
                         body['auth']['tenantName'])
        self.assertEqual(self.auth_env['OS_USERNAME'],
                         body['auth']['passwordCredentials']['username'])
        self.assertEqual(self.auth_env['OS_PASSWORD'],
                         body['auth']['passwordCredentials']['password'])

    @mock.patch('glanceclient.v1.client.Client')
    def test_auth_plugin_invocation_with_v1(self, v1_client):
        args = 'image-list'
        glance_shell = openstack_shell.OpenStackImagesShell()
        glance_shell.main(args.split())
        self._assert_auth_plugin_args()

    @mock.patch('glanceclient.v2.client.Client')
    @mock.patch.object(openstack_shell.OpenStackImagesShell, '_cache_schemas')
    def test_auth_plugin_invocation_with_v2(self,
                                            v2_client,
                                            cache_schemas):
        args = '--os-image-api-version 2 image-list'
        glance_shell = openstack_shell.OpenStackImagesShell()
        glance_shell.main(args.split())
        self._assert_auth_plugin_args()

    @mock.patch('glanceclient.v1.client.Client')
    def test_auth_plugin_invocation_with_unversioned_auth_url_with_v1(
            self, v1_client):
        args = '--os-auth-url %s image-list' % DEFAULT_UNVERSIONED_AUTH_URL
        glance_shell = openstack_shell.OpenStackImagesShell()
        glance_shell.main(args.split())
        self._assert_auth_plugin_args()

    @mock.patch('glanceclient.v2.client.Client')
    @mock.patch.object(openstack_shell.OpenStackImagesShell, '_cache_schemas')
    def test_auth_plugin_invocation_with_unversioned_auth_url_with_v2(
            self, v2_client, cache_schemas):
        args = ('--os-auth-url %s --os-image-api-version 2 '
                'image-list') % DEFAULT_UNVERSIONED_AUTH_URL
        glance_shell = openstack_shell.OpenStackImagesShell()
        glance_shell.main(args.split())
        self._assert_auth_plugin_args()

    @mock.patch('sys.stdin', side_effect=mock.MagicMock)
    @mock.patch('getpass.getpass', return_value='password')
    def test_password_prompted_with_v2(self, mock_getpass, mock_stdin):
        self.requests.post(self.token_url, exc=requests.ConnectionError)
        glance_shell = openstack_shell.OpenStackImagesShell()
        self.make_env(exclude='OS_PASSWORD')
        self.assertRaises(ks_exc.ConnectionRefused,
                          glance_shell.main, ['image-list'])
        # Make sure we are actually prompted.
        mock_getpass.assert_called_with('OS Password: ')

    @mock.patch('sys.stdin', side_effect=mock.MagicMock)
    @mock.patch('getpass.getpass', side_effect=EOFError)
    def test_password_prompted_ctrlD_with_v2(self, mock_getpass, mock_stdin):
        glance_shell = openstack_shell.OpenStackImagesShell()
        self.make_env(exclude='OS_PASSWORD')
        # We should get Command Error because we mock Ctl-D.
        self.assertRaises(exc.CommandError, glance_shell.main, ['image-list'])
        # Make sure we are actually prompted.
        mock_getpass.assert_called_with('OS Password: ')

    @mock.patch(
        'glanceclient.shell.OpenStackImagesShell._get_keystone_session')
    @mock.patch.object(openstack_shell.OpenStackImagesShell, '_cache_schemas')
    def test_no_auth_with_proj_name(self, cache_schemas, session):
        with mock.patch('glanceclient.v2.client.Client'):
            args = ('--os-project-name myname '
                    '--os-project-domain-name mydomain '
                    '--os-project-domain-id myid '
                    '--os-image-api-version 2 image-list')
            glance_shell = openstack_shell.OpenStackImagesShell()
            glance_shell.main(args.split())
            ((args), kwargs) = session.call_args
            self.assertEqual('myname', kwargs['project_name'])
            self.assertEqual('mydomain', kwargs['project_domain_name'])
            self.assertEqual('myid', kwargs['project_domain_id'])

    @mock.patch.object(openstack_shell.OpenStackImagesShell, 'main')
    def test_shell_keyboard_interrupt(self, mock_glance_shell):
        # Ensure that exit code is 130 for KeyboardInterrupt
        try:
            mock_glance_shell.side_effect = KeyboardInterrupt()
            openstack_shell.main()
        except SystemExit as ex:
            self.assertEqual(130, ex.code)

    @mock.patch('glanceclient.common.utils.exit', side_effect=utils.exit)
    def test_shell_illegal_version(self, mock_exit):
        # Only int versions are allowed on cli
        shell = openstack_shell.OpenStackImagesShell()
        argstr = '--os-image-api-version 1.1 image-list'
        try:
            shell.main(argstr.split())
        except SystemExit as ex:
            self.assertEqual(1, ex.code)
        msg = ("Invalid API version parameter. "
               "Supported values are %s" % openstack_shell.SUPPORTED_VERSIONS)
        mock_exit.assert_called_with(msg=msg)

    @mock.patch('glanceclient.common.utils.exit', side_effect=utils.exit)
    def test_shell_unsupported_version(self, mock_exit):
        # Test an integer version which is not supported (-1)
        shell = openstack_shell.OpenStackImagesShell()
        argstr = '--os-image-api-version -1 image-list'
        try:
            shell.main(argstr.split())
        except SystemExit as ex:
            self.assertEqual(1, ex.code)
        msg = ("Invalid API version parameter. "
               "Supported values are %s" % openstack_shell.SUPPORTED_VERSIONS)
        mock_exit.assert_called_with(msg=msg)

    @mock.patch.object(openstack_shell.OpenStackImagesShell,
                       'get_subcommand_parser')
    def test_shell_import_error_with_mesage(self, mock_parser):
        msg = 'Unable to import module xxx'
        mock_parser.side_effect = ImportError('%s' % msg)
        shell = openstack_shell.OpenStackImagesShell()
        argstr = '--os-image-api-version 2 image-list'
        try:
            shell.main(argstr.split())
            self.fail('No import error returned')
        except ImportError as e:
            self.assertEqual(msg, str(e))

    @mock.patch.object(openstack_shell.OpenStackImagesShell,
                       'get_subcommand_parser')
    def test_shell_import_error_default_message(self, mock_parser):
        mock_parser.side_effect = ImportError
        shell = openstack_shell.OpenStackImagesShell()
        argstr = '--os-image-api-version 2 image-list'
        try:
            shell.main(argstr.split())
            self.fail('No import error returned')
        except ImportError as e:
            msg = 'Unable to import module. Re-run with --debug for more info.'
            self.assertEqual(msg, str(e))

    @mock.patch('glanceclient.v1.client.Client')
    def test_auth_plugin_invocation_without_username_with_v1(self, v1_client):
        self.make_env(exclude='OS_USERNAME')
        args = 'image-list'
        glance_shell = openstack_shell.OpenStackImagesShell()
        self.assertRaises(exc.CommandError, glance_shell.main, args.split())

    @mock.patch('glanceclient.v2.client.Client')
    def test_auth_plugin_invocation_without_username_with_v2(self, v2_client):
        self.make_env(exclude='OS_USERNAME')
        args = '--os-image-api-version 2 image-list'
        glance_shell = openstack_shell.OpenStackImagesShell()
        self.assertRaises(exc.CommandError, glance_shell.main, args.split())

    @mock.patch('glanceclient.v1.client.Client')
    def test_auth_plugin_invocation_without_auth_url_with_v1(self, v1_client):
        self.make_env(exclude='OS_AUTH_URL')
        args = 'image-list'
        glance_shell = openstack_shell.OpenStackImagesShell()
        self.assertRaises(exc.CommandError, glance_shell.main, args.split())

    @mock.patch('glanceclient.v2.client.Client')
    def test_auth_plugin_invocation_without_auth_url_with_v2(self, v2_client):
        self.make_env(exclude='OS_AUTH_URL')
        args = '--os-image-api-version 2 image-list'
        glance_shell = openstack_shell.OpenStackImagesShell()
        self.assertRaises(exc.CommandError, glance_shell.main, args.split())

    @mock.patch('glanceclient.v1.client.Client')
    def test_auth_plugin_invocation_without_tenant_with_v1(self, v1_client):
        if 'OS_TENANT_NAME' in os.environ:
            self.make_env(exclude='OS_TENANT_NAME')
        if 'OS_PROJECT_ID' in os.environ:
            self.make_env(exclude='OS_PROJECT_ID')
        args = 'image-list'
        glance_shell = openstack_shell.OpenStackImagesShell()
        self.assertRaises(exc.CommandError, glance_shell.main, args.split())

    @mock.patch('glanceclient.v2.client.Client')
    def test_auth_plugin_invocation_without_tenant_with_v2(self, v2_client):
        if 'OS_TENANT_NAME' in os.environ:
            self.make_env(exclude='OS_TENANT_NAME')
        if 'OS_PROJECT_ID' in os.environ:
            self.make_env(exclude='OS_PROJECT_ID')
        args = '--os-image-api-version 2 image-list'
        glance_shell = openstack_shell.OpenStackImagesShell()
        self.assertRaises(exc.CommandError, glance_shell.main, args.split())


class ShellTestWithKeystoneV3Auth(ShellTest):
    # auth environment to use
    auth_env = FAKE_V3_ENV.copy()
    token_url = DEFAULT_V3_AUTH_URL + '/auth/tokens'

    def _assert_auth_plugin_args(self):
        self.assertFalse(self.v2_auth.called)
        self.assertEqual(1, self.v3_auth.call_count)

        body = json.loads(self.v3_auth.last_request.body)
        user = body['auth']['identity']['password']['user']

        self.assertEqual(self.auth_env['OS_USERNAME'], user['name'])
        self.assertEqual(self.auth_env['OS_PASSWORD'], user['password'])
        self.assertEqual(self.auth_env['OS_USER_DOMAIN_NAME'],
                         user['domain']['name'])
        self.assertEqual(self.auth_env['OS_PROJECT_ID'],
                         body['auth']['scope']['project']['id'])

    @mock.patch('glanceclient.v1.client.Client')
    def test_auth_plugin_invocation_with_v1(self, v1_client):
        args = 'image-list'
        glance_shell = openstack_shell.OpenStackImagesShell()
        glance_shell.main(args.split())
        self._assert_auth_plugin_args()

    @mock.patch('glanceclient.v2.client.Client')
    @mock.patch.object(openstack_shell.OpenStackImagesShell, '_cache_schemas')
    def test_auth_plugin_invocation_with_v2(self, v2_client, cache_schemas):
        args = '--os-image-api-version 2 image-list'
        glance_shell = openstack_shell.OpenStackImagesShell()
        glance_shell.main(args.split())
        self._assert_auth_plugin_args()

    @mock.patch('keystoneclient.discover.Discover',
                side_effect=ks_exc.ClientException())
    def test_api_discovery_failed_with_unversioned_auth_url(self,
                                                            discover):
        args = '--os-auth-url %s image-list' % DEFAULT_UNVERSIONED_AUTH_URL
        glance_shell = openstack_shell.OpenStackImagesShell()
        self.assertRaises(exc.CommandError, glance_shell.main, args.split())

    def test_bash_completion(self):
        stdout, stderr = self.shell('bash_completion')
        # just check we have some output
        required = [
            '--status',
            'image-create',
            'help',
            '--size']
        for r in required:
            self.assertIn(r, stdout.split())
        avoided = [
            'bash_completion',
            'bash-completion']
        for r in avoided:
            self.assertNotIn(r, stdout.split())


class ShellCacheSchemaTest(testutils.TestCase):
    def setUp(self):
        super(ShellCacheSchemaTest, self).setUp()
        self._mock_client_setup()
        self._mock_shell_setup()
        self.cache_dir = '/dir_for_cached_schema'
        self.cache_files = [self.cache_dir + '/image_schema.json',
                            self.cache_dir + '/namespace_schema.json',
                            self.cache_dir + '/resource_type_schema.json']

    def tearDown(self):
        super(ShellCacheSchemaTest, self).tearDown()

    def _mock_client_setup(self):
        self.schema_dict = {
            'name': 'image',
            'properties': {
                'name': {'type': 'string', 'description': 'Name of image'},
            },
        }

        self.client = mock.Mock()
        self.client.schemas.get.return_value = schemas.Schema(self.schema_dict)

    def _mock_shell_setup(self):
        mocked_get_client = mock.MagicMock(return_value=self.client)
        self.shell = openstack_shell.OpenStackImagesShell()
        self.shell._get_versioned_client = mocked_get_client

    def _make_args(self, args):
        class Args():
            def __init__(self, entries):
                self.__dict__.update(entries)

        return Args(args)

    @mock.patch('six.moves.builtins.open', new=mock.mock_open(), create=True)
    @mock.patch('os.path.exists', return_value=True)
    def test_cache_schemas_gets_when_forced(self, exists_mock):
        options = {
            'get_schema': True
        }

        self.shell._cache_schemas(self._make_args(options),
                                  home_dir=self.cache_dir)

        self.assertEqual(12, open.mock_calls.__len__())
        self.assertEqual(mock.call(self.cache_files[0], 'w'),
                         open.mock_calls[0])
        self.assertEqual(mock.call(self.cache_files[1], 'w'),
                         open.mock_calls[4])
        self.assertEqual(mock.call().write(json.dumps(self.schema_dict)),
                         open.mock_calls[2])
        self.assertEqual(mock.call().write(json.dumps(self.schema_dict)),
                         open.mock_calls[6])

    @mock.patch('six.moves.builtins.open', new=mock.mock_open(), create=True)
    @mock.patch('os.path.exists', side_effect=[True, False, False, False])
    def test_cache_schemas_gets_when_not_exists(self, exists_mock):
        options = {
            'get_schema': False
        }

        self.shell._cache_schemas(self._make_args(options),
                                  home_dir=self.cache_dir)

        self.assertEqual(12, open.mock_calls.__len__())
        self.assertEqual(mock.call(self.cache_files[0], 'w'),
                         open.mock_calls[0])
        self.assertEqual(mock.call(self.cache_files[1], 'w'),
                         open.mock_calls[4])
        self.assertEqual(mock.call().write(json.dumps(self.schema_dict)),
                         open.mock_calls[2])
        self.assertEqual(mock.call().write(json.dumps(self.schema_dict)),
                         open.mock_calls[6])

    @mock.patch('six.moves.builtins.open', new=mock.mock_open(), create=True)
    @mock.patch('os.path.exists', return_value=True)
    def test_cache_schemas_leaves_when_present_not_forced(self, exists_mock):
        options = {
            'get_schema': False
        }

        self.shell._cache_schemas(self._make_args(options),
                                  home_dir=self.cache_dir)

        os.path.exists.assert_any_call(self.cache_dir)
        os.path.exists.assert_any_call(self.cache_files[0])
        os.path.exists.assert_any_call(self.cache_files[1])
        self.assertEqual(4, exists_mock.call_count)
        self.assertEqual(0, open.mock_calls.__len__())
