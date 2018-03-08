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
from collections import OrderedDict
import hashlib
import logging
import os
import sys
import traceback
import uuid

import fixtures
from keystoneauth1 import exceptions as ks_exc
from keystoneauth1 import fixture as ks_fixture
import mock
from requests_mock.contrib import fixture as rm_fixture
import six

from glanceclient.common import utils
from glanceclient import exc
from glanceclient import shell as openstack_shell
from glanceclient.tests.unit.v2.fixtures import image_show_fixture
from glanceclient.tests.unit.v2.fixtures import image_versions_fixture
from glanceclient.tests import utils as testutils

# NOTE (esheffield) Used for the schema caching tests
from glanceclient.v2 import schemas as schemas
import json


DEFAULT_IMAGE_URL = 'http://127.0.0.1:9292/'
DEFAULT_IMAGE_URL_INTERNAL = 'http://127.0.0.1:9191/'
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
DEFAULT_SERVICE_TYPE = 'image'
DEFAULT_ENDPOINT_TYPE = 'public'

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

FAKE_V4_ENV = {'OS_USERNAME': DEFAULT_USERNAME,
               'OS_PASSWORD': DEFAULT_PASSWORD,
               'OS_PROJECT_ID': DEFAULT_PROJECT_ID,
               'OS_USER_DOMAIN_NAME': DEFAULT_USER_DOMAIN_NAME,
               'OS_AUTH_URL': DEFAULT_V3_AUTH_URL,
               'OS_SERVICE_TYPE': DEFAULT_SERVICE_TYPE,
               'OS_ENDPOINT_TYPE': DEFAULT_ENDPOINT_TYPE,
               'OS_AUTH_TOKEN': DEFAULT_AUTH_TOKEN}

TOKEN_ID = uuid.uuid4().hex

V2_TOKEN = ks_fixture.V2Token(token_id=TOKEN_ID)
V2_TOKEN.set_scope()
_s = V2_TOKEN.add_service('image', name='glance')
_s.add_endpoint(DEFAULT_IMAGE_URL)

V3_TOKEN = ks_fixture.V3Token()
V3_TOKEN.set_project_scope()
_s = V3_TOKEN.add_service('image', name='glance')
_s.add_standard_endpoints(public=DEFAULT_IMAGE_URL,
                          internal=DEFAULT_IMAGE_URL_INTERNAL)


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
        self.requests.get(DEFAULT_UNVERSIONED_AUTH_URL,
                          json=json_list,
                          status_code=300)

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

    def test_fixup_subcommand(self):
        arglist = [u'image-list', u'--help']
        if six.PY2:
            expected_arglist = [b'image-list', u'--help']
        elif six.PY3:
            expected_arglist = [u'image-list', u'--help']

        openstack_shell.OpenStackImagesShell._fixup_subcommand(
            arglist, arglist
        )
        self.assertEqual(expected_arglist, arglist)

    def test_fixup_subcommand_with_options_preceding(self):
        arglist = [u'--os-auth-token', u'abcdef', u'image-list', u'--help']
        unknown = arglist[2:]
        if six.PY2:
            expected_arglist = [
                u'--os-auth-token', u'abcdef', b'image-list', u'--help'
            ]
        elif six.PY3:
            expected_arglist = [
                u'--os-auth-token', u'abcdef', u'image-list', u'--help'
            ]

        openstack_shell.OpenStackImagesShell._fixup_subcommand(
            unknown, arglist
        )
        self.assertEqual(expected_arglist, arglist)

    def test_help_unknown_command(self):
        shell = openstack_shell.OpenStackImagesShell()
        argstr = '--os-image-api-version 2 help foofoo'
        self.assertRaises(exc.CommandError, shell.main, argstr.split())

    @mock.patch('sys.stdout', six.StringIO())
    @mock.patch('sys.stderr', six.StringIO())
    @mock.patch('sys.argv', ['glance', 'help', 'foofoo'])
    def test_no_stacktrace_when_debug_disabled(self):
        with mock.patch.object(traceback, 'print_exc') as mock_print_exc:
            try:
                openstack_shell.main()
            except SystemExit:
                pass
            self.assertFalse(mock_print_exc.called)

    @mock.patch('sys.stdout', six.StringIO())
    @mock.patch('sys.stderr', six.StringIO())
    @mock.patch('sys.argv', ['glance', 'help', 'foofoo'])
    def test_stacktrace_when_debug_enabled_by_env(self):
        old_environment = os.environ.copy()
        os.environ = {'GLANCECLIENT_DEBUG': '1'}
        try:
            with mock.patch.object(traceback, 'print_exc') as mock_print_exc:
                try:
                    openstack_shell.main()
                except SystemExit:
                    pass
                self.assertTrue(mock_print_exc.called)
        finally:
            os.environ = old_environment

    @mock.patch('sys.stdout', six.StringIO())
    @mock.patch('sys.stderr', six.StringIO())
    @mock.patch('sys.argv', ['glance', '--debug', 'help', 'foofoo'])
    def test_stacktrace_when_debug_enabled(self):
        with mock.patch.object(traceback, 'print_exc') as mock_print_exc:
            try:
                openstack_shell.main()
            except SystemExit:
                pass
            self.assertTrue(mock_print_exc.called)

    def test_help(self):
        shell = openstack_shell.OpenStackImagesShell()
        argstr = '--os-image-api-version 2 help'
        with mock.patch.object(shell, '_get_keystone_auth_plugin') as et_mock:
            actual = shell.main(argstr.split())
            self.assertEqual(0, actual)
            self.assertFalse(et_mock.called)

    def test_blank_call(self):
        shell = openstack_shell.OpenStackImagesShell()
        with mock.patch.object(shell, '_get_keystone_auth_plugin') as et_mock:
            actual = shell.main('')
            self.assertEqual(0, actual)
            self.assertFalse(et_mock.called)

    def test_help_on_subcommand_error(self):
        self.assertRaises(exc.CommandError, shell,
                          '--os-image-api-version 2 help bad')

    def test_help_v2_no_schema(self):
        shell = openstack_shell.OpenStackImagesShell()
        argstr = '--os-image-api-version 2 help image-create'
        with mock.patch.object(shell, '_get_keystone_auth_plugin') as et_mock:
            actual = shell.main(argstr.split())
            self.assertEqual(0, actual)
            self.assertNotIn('<unavailable>', actual)
            self.assertFalse(et_mock.called)

        argstr = '--os-image-api-version 2 help md-namespace-create'
        with mock.patch.object(shell, '_get_keystone_auth_plugin') as et_mock:
            actual = shell.main(argstr.split())
            self.assertEqual(0, actual)
            self.assertNotIn('<unavailable>', actual)
            self.assertFalse(et_mock.called)

        argstr = '--os-image-api-version 2 help md-resource-type-associate'
        with mock.patch.object(shell, '_get_keystone_auth_plugin') as et_mock:
            actual = shell.main(argstr.split())
            self.assertEqual(0, actual)
            self.assertNotIn('<unavailable>', actual)
            self.assertFalse(et_mock.called)

    def test_get_base_parser(self):
        test_shell = openstack_shell.OpenStackImagesShell()
        # NOTE(stevemar): Use the current sys.argv for base_parser since it
        # doesn't matter for this test, it just needs to initialize the CLI
        actual_parser = test_shell.get_base_parser(sys.argv)
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
        args = ('--os-image-api-version 2 '
                '--os-cert mycert '
                '--os-key mykey image-list')
        shell(args)
        assert mock_versioned_client.called
        ((api_version, args), kwargs) = mock_versioned_client.call_args
        self.assertEqual('mycert', args.os_cert)
        self.assertEqual('mykey', args.os_key)

    @mock.patch('glanceclient.v1.client.Client')
    def test_no_auth_with_token_and_image_url_with_v1(self, v1_client):
        # test no authentication is required if both token and endpoint url
        # are specified
        args = ('--os-image-api-version 1 --os-auth-token mytoken'
                ' --os-image-url https://image:1234/v1 image-list')
        glance_shell = openstack_shell.OpenStackImagesShell()
        glance_shell.main(args.split())
        assert v1_client.called
        (args, kwargs) = v1_client.call_args
        self.assertEqual('mytoken', kwargs['token'])
        self.assertEqual('https://image:1234', args[0])

    @mock.patch('glanceclient.v2.client.Client')
    def test_no_auth_with_token_and_image_url_with_v2(self, v2_client):
        # test no authentication is required if both token and endpoint url
        # are specified
        args = ('--os-image-api-version 2 --os-auth-token mytoken '
                '--os-image-url https://image:1234 image-list')
        glance_shell = openstack_shell.OpenStackImagesShell()
        glance_shell.main(args.split())
        self.assertTrue(v2_client.called)
        (args, kwargs) = v2_client.call_args
        self.assertEqual('mytoken', kwargs['token'])
        self.assertEqual('https://image:1234', args[0])

    def _assert_auth_plugin_args(self):
        # make sure our auth plugin is invoked with the correct args
        self.assertFalse(self.v3_auth.called)

        body = json.loads(self.v2_auth.last_request.body)

        self.assertEqual(self.auth_env['OS_TENANT_NAME'],
                         body['auth']['tenantName'])
        self.assertEqual(self.auth_env['OS_USERNAME'],
                         body['auth']['passwordCredentials']['username'])
        self.assertEqual(self.auth_env['OS_PASSWORD'],
                         body['auth']['passwordCredentials']['password'])

    @mock.patch.object(openstack_shell.OpenStackImagesShell, '_cache_schemas',
                       return_value=False)
    @mock.patch('glanceclient.v2.client.Client')
    def test_auth_plugin_invocation_without_version(self,
                                                    v2_client,
                                                    cache_schemas):

        cli2 = mock.MagicMock()
        v2_client.return_value = cli2
        cli2.http_client.get.return_value = (None, {'versions':
                                                    [{'id': 'v2'}]})

        args = 'image-list'
        glance_shell = openstack_shell.OpenStackImagesShell()
        glance_shell.main(args.split())
        # NOTE(flaper87): this currently calls auth twice since it'll
        # authenticate to get the version list *and* to execute the command.
        # This is not the ideal behavior and it should be fixed in a follow
        # up patch.

    @mock.patch('glanceclient.v1.client.Client')
    def test_auth_plugin_invocation_with_v1(self, v1_client):
        args = '--os-image-api-version 1 image-list'
        glance_shell = openstack_shell.OpenStackImagesShell()
        glance_shell.main(args.split())
        self.assertEqual(0, self.v2_auth.call_count)

    @mock.patch('glanceclient.v2.client.Client')
    def test_auth_plugin_invocation_with_v2(self,
                                            v2_client):
        args = '--os-image-api-version 2 image-list'
        glance_shell = openstack_shell.OpenStackImagesShell()
        glance_shell.main(args.split())
        self.assertEqual(0, self.v2_auth.call_count)

    @mock.patch('glanceclient.v1.client.Client')
    def test_auth_plugin_invocation_with_unversioned_auth_url_with_v1(
            self, v1_client):
        args = ('--os-image-api-version 1 --os-auth-url %s image-list' %
                DEFAULT_UNVERSIONED_AUTH_URL)
        glance_shell = openstack_shell.OpenStackImagesShell()
        glance_shell.main(args.split())

    @mock.patch('glanceclient.v2.client.Client')
    @mock.patch.object(openstack_shell.OpenStackImagesShell, '_cache_schemas',
                       return_value=False)
    def test_auth_plugin_invocation_with_unversioned_auth_url_with_v2(
            self, v2_client, cache_schemas):
        args = ('--os-auth-url %s --os-image-api-version 2 '
                'image-list') % DEFAULT_UNVERSIONED_AUTH_URL
        glance_shell = openstack_shell.OpenStackImagesShell()
        glance_shell.main(args.split())

    @mock.patch('glanceclient.Client')
    def test_endpoint_token_no_auth_req(self, mock_client):

        def verify_input(version=None, endpoint=None, *args, **kwargs):
            self.assertIn('token', kwargs)
            self.assertEqual(TOKEN_ID, kwargs['token'])
            self.assertEqual(DEFAULT_IMAGE_URL, endpoint)
            return mock.MagicMock()

        mock_client.side_effect = verify_input
        glance_shell = openstack_shell.OpenStackImagesShell()
        args = ['--os-image-api-version', '2',
                '--os-auth-token', TOKEN_ID,
                '--os-image-url', DEFAULT_IMAGE_URL,
                'image-list']

        glance_shell.main(args)
        self.assertEqual(1, mock_client.call_count)

    @mock.patch('sys.stdin', side_effect=mock.MagicMock)
    @mock.patch('getpass.getpass', side_effect=EOFError)
    @mock.patch('glanceclient.v2.client.Client')
    def test_password_prompted_ctrlD_with_v2(self, v2_client,
                                             mock_getpass, mock_stdin):
        cli2 = mock.MagicMock()
        v2_client.return_value = cli2
        cli2.http_client.get.return_value = (None, {'versions': []})

        glance_shell = openstack_shell.OpenStackImagesShell()
        self.make_env(exclude='OS_PASSWORD')
        # We should get Command Error because we mock Ctl-D.
        self.assertRaises(exc.CommandError, glance_shell.main, ['image-list'])
        # Make sure we are actually prompted.
        mock_getpass.assert_called_with('OS Password: ')

    @mock.patch(
        'glanceclient.shell.OpenStackImagesShell._get_keystone_auth_plugin')
    @mock.patch.object(openstack_shell.OpenStackImagesShell, '_cache_schemas',
                       return_value=False)
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

    @mock.patch('glanceclient.v2.client.Client')
    @mock.patch('glanceclient.v1.images.ImageManager.list')
    def test_shell_v1_fallback_from_v2(self, v1_imgs, v2_client):
        self.make_env()
        cli2 = mock.MagicMock()
        v2_client.return_value = cli2
        cli2.http_client.get.return_value = (None, {'versions': []})
        args = 'image-list'
        glance_shell = openstack_shell.OpenStackImagesShell()
        glance_shell.main(args.split())
        self.assertFalse(cli2.schemas.get.called)
        self.assertTrue(v1_imgs.called)

    @mock.patch.object(openstack_shell.OpenStackImagesShell,
                       '_cache_schemas')
    @mock.patch('glanceclient.v2.client.Client')
    def test_shell_no_fallback_from_v2(self, v2_client, cache_schemas):
        self.make_env()
        cli2 = mock.MagicMock()
        v2_client.return_value = cli2
        cli2.http_client.get.return_value = (None,
                                             {'versions': [{'id': 'v2'}]})
        cache_schemas.return_value = False
        args = 'image-list'
        glance_shell = openstack_shell.OpenStackImagesShell()
        glance_shell.main(args.split())
        self.assertTrue(cli2.images.list.called)

    @mock.patch('glanceclient.v1.client.Client')
    def test_auth_plugin_invocation_without_username_with_v1(self, v1_client):
        self.make_env(exclude='OS_USERNAME')
        args = '--os-image-api-version 2 image-list'
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
        args = '--os-image-api-version 1 image-list'
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
        args = '--os-image-api-version 1 image-list'
        glance_shell = openstack_shell.OpenStackImagesShell()
        self.assertRaises(exc.CommandError, glance_shell.main, args.split())

    @mock.patch('glanceclient.v2.client.Client')
    @mock.patch.object(openstack_shell.OpenStackImagesShell, '_cache_schemas',
                       return_value=False)
    def test_auth_plugin_invocation_without_tenant_with_v2(self, v2_client,
                                                           cache_schemas):
        if 'OS_TENANT_NAME' in os.environ:
            self.make_env(exclude='OS_TENANT_NAME')
        if 'OS_PROJECT_ID' in os.environ:
            self.make_env(exclude='OS_PROJECT_ID')
        args = '--os-image-api-version 2 image-list'
        glance_shell = openstack_shell.OpenStackImagesShell()
        self.assertRaises(exc.CommandError, glance_shell.main, args.split())

    @mock.patch('sys.argv', ['glance'])
    @mock.patch('sys.stdout', six.StringIO())
    @mock.patch('sys.stderr', six.StringIO())
    def test_main_noargs(self):
        # Ensure that main works with no command-line arguments
        try:
            openstack_shell.main()
        except SystemExit:
            self.fail('Unexpected SystemExit')

        # We expect the normal v2 usage as a result
        expected = ['Command-line interface to the OpenStack Images API',
                    'image-list',
                    'image-deactivate',
                    'location-add']
        for output in expected:
            self.assertIn(output,
                          sys.stdout.getvalue())

    @mock.patch('glanceclient.v2.client.Client')
    @mock.patch('glanceclient.v1.shell.do_image_list')
    @mock.patch('glanceclient.shell.logging.basicConfig')
    def test_setup_debug(self, conf, func, v2_client):
        cli2 = mock.MagicMock()
        v2_client.return_value = cli2
        cli2.http_client.get.return_value = (None, {'versions': []})
        args = '--debug image-list'
        glance_shell = openstack_shell.OpenStackImagesShell()
        glance_shell.main(args.split())
        glance_logger = logging.getLogger('glanceclient')
        self.assertEqual(glance_logger.getEffectiveLevel(), logging.DEBUG)
        conf.assert_called_with(level=logging.DEBUG)


class ShellTestWithKeystoneV3Auth(ShellTest):
    # auth environment to use
    auth_env = FAKE_V3_ENV.copy()
    token_url = DEFAULT_V3_AUTH_URL + '/auth/tokens'

    def _assert_auth_plugin_args(self):
        self.assertFalse(self.v2_auth.called)

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
        args = '--os-image-api-version 1 image-list'
        glance_shell = openstack_shell.OpenStackImagesShell()
        glance_shell.main(args.split())
        self.assertEqual(0, self.v3_auth.call_count)

    @mock.patch('glanceclient.v2.client.Client')
    def test_auth_plugin_invocation_with_v2(self, v2_client):
        args = '--os-image-api-version 2 image-list'
        glance_shell = openstack_shell.OpenStackImagesShell()
        glance_shell.main(args.split())
        self.assertEqual(0, self.v3_auth.call_count)

    @mock.patch('keystoneauth1.discover.Discover',
                side_effect=ks_exc.ClientException())
    def test_api_discovery_failed_with_unversioned_auth_url(self,
                                                            discover):
        args = ('--os-image-api-version 2 --os-auth-url %s image-list'
                % DEFAULT_UNVERSIONED_AUTH_URL)
        glance_shell = openstack_shell.OpenStackImagesShell()
        self.assertRaises(exc.CommandError, glance_shell.main, args.split())

    def test_bash_completion(self):
        stdout, stderr = self.shell('--os-image-api-version 2 bash_completion')
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


class ShellTestWithNoOSImageURLPublic(ShellTestWithKeystoneV3Auth):
    # auth environment to use
    # default uses public
    auth_env = FAKE_V4_ENV.copy()

    def setUp(self):
        super(ShellTestWithNoOSImageURLPublic, self).setUp()
        self.image_url = DEFAULT_IMAGE_URL
        self.requests.get(DEFAULT_IMAGE_URL + 'v2/images',
                          text='{"images": []}')

    @mock.patch('glanceclient.v1.client.Client')
    def test_auth_plugin_invocation_with_v1(self, v1_client):
        args = '--os-image-api-version 1 image-list'
        glance_shell = openstack_shell.OpenStackImagesShell()
        glance_shell.main(args.split())
        self.assertEqual(1, self.v3_auth.call_count)
        self._assert_auth_plugin_args()

    @mock.patch('glanceclient.v2.client.Client')
    def test_auth_plugin_invocation_with_v2(self, v2_client):
        args = '--os-image-api-version 2 image-list'
        glance_shell = openstack_shell.OpenStackImagesShell()
        glance_shell.main(args.split())
        self.assertEqual(1, self.v3_auth.call_count)
        self._assert_auth_plugin_args()

    @mock.patch('glanceclient.v2.client.Client')
    def test_endpoint_from_interface(self, v2_client):
        args = ('--os-image-api-version 2 image-list')
        glance_shell = openstack_shell.OpenStackImagesShell()
        glance_shell.main(args.split())
        assert v2_client.called
        (args, kwargs) = v2_client.call_args
        self.assertEqual(self.image_url, kwargs['endpoint_override'])

    def test_endpoint_real_from_interface(self):
        args = ('--os-image-api-version 2 image-list')
        glance_shell = openstack_shell.OpenStackImagesShell()
        glance_shell.main(args.split())
        self.assertEqual(self.requests.request_history[2].url,
                         self.image_url + "v2/images?limit=20&"
                         "sort_key=name&sort_dir=asc")


class ShellTestWithNoOSImageURLInternal(ShellTestWithNoOSImageURLPublic):
    # auth environment to use
    # this uses internal
    FAKE_V5_ENV = FAKE_V4_ENV.copy()
    FAKE_V5_ENV['OS_ENDPOINT_TYPE'] = 'internal'
    auth_env = FAKE_V5_ENV.copy()

    def setUp(self):
        super(ShellTestWithNoOSImageURLPublic, self).setUp()
        self.image_url = DEFAULT_IMAGE_URL_INTERNAL
        self.requests.get(DEFAULT_IMAGE_URL_INTERNAL + 'v2/images',
                          text='{"images": []}')


class ShellCacheSchemaTest(testutils.TestCase):
    def setUp(self):
        super(ShellCacheSchemaTest, self).setUp()
        self._mock_client_setup()
        self._mock_shell_setup()
        self.cache_dir = '/dir_for_cached_schema'
        self.os_auth_url = 'http://localhost:5000/v2'
        url_hex = hashlib.sha1(self.os_auth_url.encode('utf-8')).hexdigest()
        self.prefix_path = (self.cache_dir + '/' + url_hex)
        self.cache_files = [self.prefix_path + '/image_schema.json',
                            self.prefix_path + '/namespace_schema.json',
                            self.prefix_path + '/resource_type_schema.json']

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
        schema_odict = OrderedDict(self.schema_dict)
        self.client.schemas.get.return_value = schemas.Schema(schema_odict)

    def _mock_shell_setup(self):
        self.shell = openstack_shell.OpenStackImagesShell()
        self.shell._get_versioned_client = mock.create_autospec(
            self.shell._get_versioned_client, return_value=self.client,
            spec_set=True
        )

    def _make_args(self, args):
        class Args(object):
            def __init__(self, entries):
                self.__dict__.update(entries)

        return Args(args)

    @mock.patch('six.moves.builtins.open', new=mock.mock_open(), create=True)
    @mock.patch('os.path.exists', return_value=True)
    def test_cache_schemas_gets_when_forced(self, exists_mock):
        options = {
            'get_schema': True,
            'os_auth_url': self.os_auth_url
        }
        schema_odict = OrderedDict(self.schema_dict)

        args = self._make_args(options)
        client = self.shell._get_versioned_client('2', args)
        self.shell._cache_schemas(args, client, home_dir=self.cache_dir)

        self.assertEqual(12, open.mock_calls.__len__())
        self.assertEqual(mock.call(self.cache_files[0], 'w'),
                         open.mock_calls[0])
        self.assertEqual(mock.call(self.cache_files[1], 'w'),
                         open.mock_calls[4])
        self.assertEqual(mock.call().write(json.dumps(schema_odict)),
                         open.mock_calls[2])
        self.assertEqual(mock.call().write(json.dumps(schema_odict)),
                         open.mock_calls[6])

    @mock.patch('six.moves.builtins.open', new=mock.mock_open(), create=True)
    @mock.patch('os.path.exists', side_effect=[True, False, False, False])
    def test_cache_schemas_gets_when_not_exists(self, exists_mock):
        options = {
            'get_schema': False,
            'os_auth_url': self.os_auth_url
        }
        schema_odict = OrderedDict(self.schema_dict)

        args = self._make_args(options)
        client = self.shell._get_versioned_client('2', args)
        self.shell._cache_schemas(args, client, home_dir=self.cache_dir)

        self.assertEqual(12, open.mock_calls.__len__())
        self.assertEqual(mock.call(self.cache_files[0], 'w'),
                         open.mock_calls[0])
        self.assertEqual(mock.call(self.cache_files[1], 'w'),
                         open.mock_calls[4])
        self.assertEqual(mock.call().write(json.dumps(schema_odict)),
                         open.mock_calls[2])
        self.assertEqual(mock.call().write(json.dumps(schema_odict)),
                         open.mock_calls[6])

    @mock.patch('six.moves.builtins.open', new=mock.mock_open(), create=True)
    @mock.patch('os.path.exists', return_value=True)
    def test_cache_schemas_leaves_when_present_not_forced(self, exists_mock):
        options = {
            'get_schema': False,
            'os_auth_url': self.os_auth_url
        }

        client = mock.MagicMock()
        self.shell._cache_schemas(self._make_args(options),
                                  client, home_dir=self.cache_dir)

        exists_mock.assert_has_calls([
            mock.call(self.prefix_path),
            mock.call(self.cache_files[0]),
            mock.call(self.cache_files[1]),
            mock.call(self.cache_files[2])
        ])
        self.assertEqual(4, exists_mock.call_count)
        self.assertEqual(0, open.mock_calls.__len__())

    @mock.patch('six.moves.builtins.open', new=mock.mock_open(), create=True)
    @mock.patch('os.path.exists', return_value=True)
    def test_cache_schemas_leaves_auto_switch(self, exists_mock):
        options = {
            'get_schema': True,
            'os_auth_url': self.os_auth_url
        }

        self.client.schemas.get.return_value = Exception()

        client = mock.MagicMock()
        switch_version = self.shell._cache_schemas(self._make_args(options),
                                                   client,
                                                   home_dir=self.cache_dir)
        self.assertEqual(True, switch_version)


class ShellTestRequests(testutils.TestCase):
    """Shell tests using the requests mock library."""
    def _make_args(self, args):
        # NOTE(venkatesh): this conversion from a dict to an object
        # is required because the test_shell.do_xxx(gc, args) methods
        # expects the args to be attributes of an object. If passed as
        # dict directly, it throws an AttributeError.
        class Args(object):
            def __init__(self, entries):
                self.__dict__.update(entries)

        return Args(args)

    def setUp(self):
        super(ShellTestRequests, self).setUp()
        self._old_env = os.environ
        os.environ = {}

    def tearDown(self):
        super(ShellTestRequests, self).tearDown()
        os.environ = self._old_env

    def test_download_has_no_stray_output_to_stdout(self):
        """Regression test for bug 1488914"""
        saved_stdout = sys.stdout
        try:
            sys.stdout = output = testutils.FakeNoTTYStdout()
            id = image_show_fixture['id']
            self.requests = self.useFixture(rm_fixture.Fixture())
            self.requests.get('http://example.com/versions',
                              json=image_versions_fixture)

            headers = {'Content-Length': '4',
                       'Content-type': 'application/octet-stream'}
            fake = testutils.FakeResponse(headers, six.StringIO('DATA'))
            self.requests.get('http://example.com/v1/images/%s' % id,
                              raw=fake)

            self.requests.get('http://example.com/v1/images/detail'
                              '?sort_key=name&sort_dir=asc&limit=20')

            headers = {'X-Image-Meta-Id': id}
            self.requests.head('http://example.com/v1/images/%s' % id,
                               headers=headers)

            with mock.patch.object(openstack_shell.OpenStackImagesShell,
                                   '_cache_schemas') as mocked_cache_schema:
                mocked_cache_schema.return_value = True
                shell = openstack_shell.OpenStackImagesShell()
                argstr = ('--os-auth-token faketoken '
                          '--os-image-url http://example.com '
                          'image-download %s' % id)
                shell.main(argstr.split())
                self.assertTrue(mocked_cache_schema.called)
            # Ensure we have *only* image data
            self.assertEqual('DATA', output.getvalue())
        finally:
            sys.stdout = saved_stdout

    def test_v1_download_has_no_stray_output_to_stdout(self):
        """Ensure no stray print statements corrupt the image"""
        saved_stdout = sys.stdout
        try:
            sys.stdout = output = testutils.FakeNoTTYStdout()
            id = image_show_fixture['id']

            self.requests = self.useFixture(rm_fixture.Fixture())
            headers = {'X-Image-Meta-Id': id}
            self.requests.head('http://example.com/v1/images/%s' % id,
                               headers=headers)

            headers = {'Content-Length': '4',
                       'Content-type': 'application/octet-stream'}
            fake = testutils.FakeResponse(headers, six.StringIO('DATA'))
            self.requests.get('http://example.com/v1/images/%s' % id,
                              headers=headers, raw=fake)

            shell = openstack_shell.OpenStackImagesShell()
            argstr = ('--os-image-api-version 1 --os-auth-token faketoken '
                      '--os-image-url http://example.com '
                      'image-download %s' % id)
            shell.main(argstr.split())
            # Ensure we have *only* image data
            self.assertEqual('DATA', output.getvalue())
        finally:
            sys.stdout = saved_stdout

    def test_v2_download_has_no_stray_output_to_stdout(self):
        """Ensure no stray print statements corrupt the image"""
        saved_stdout = sys.stdout
        try:
            sys.stdout = output = testutils.FakeNoTTYStdout()
            id = image_show_fixture['id']
            headers = {'Content-Length': '4',
                       'Content-type': 'application/octet-stream'}
            fake = testutils.FakeResponse(headers, six.StringIO('DATA'))

            self.requests = self.useFixture(rm_fixture.Fixture())
            self.requests.get('http://example.com/v2/images/%s/file' % id,
                              headers=headers, raw=fake)

            shell = openstack_shell.OpenStackImagesShell()
            argstr = ('--os-image-api-version 2 --os-auth-token faketoken '
                      '--os-image-url http://example.com '
                      'image-download %s' % id)
            shell.main(argstr.split())
            # Ensure we have *only* image data
            self.assertEqual('DATA', output.getvalue())
        finally:
            sys.stdout = saved_stdout
