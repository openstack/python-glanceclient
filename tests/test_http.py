# Copyright 2012 OpenStack Foundation
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
import json

import mock
from mox3 import mox
import requests
import six
from six.moves.urllib import parse
import testtools
import types

import glanceclient
from glanceclient.common import http
from glanceclient.common import https
from glanceclient import exc
from tests import utils


class TestClient(testtools.TestCase):

    def setUp(self):
        super(TestClient, self).setUp()
        self.mock = mox.Mox()
        self.mock.StubOutWithMock(requests.Session, 'request')

        self.endpoint = 'http://example.com:9292'
        self.client = http.HTTPClient(self.endpoint, token=u'abc123')

    def tearDown(self):
        super(TestClient, self).tearDown()
        self.mock.UnsetStubs()

    def test_identity_headers_and_token(self):
        identity_headers = {
            'X-Auth-Token': 'auth_token',
            'X-User-Id': 'user',
            'X-Tenant-Id': 'tenant',
            'X-Roles': 'roles',
            'X-Identity-Status': 'Confirmed',
            'X-Service-Catalog': 'service_catalog',
        }
        #with token
        kwargs = {'token': u'fake-token',
                  'identity_headers': identity_headers}
        http_client_object = http.HTTPClient(self.endpoint, **kwargs)
        self.assertEqual('auth_token', http_client_object.auth_token)
        self.assertTrue(http_client_object.identity_headers.
                        get('X-Auth-Token') is None)

    def test_identity_headers_and_no_token_in_header(self):
        identity_headers = {
            'X-User-Id': 'user',
            'X-Tenant-Id': 'tenant',
            'X-Roles': 'roles',
            'X-Identity-Status': 'Confirmed',
            'X-Service-Catalog': 'service_catalog',
        }
        #without X-Auth-Token in identity headers
        kwargs = {'token': u'fake-token',
                  'identity_headers': identity_headers}
        http_client_object = http.HTTPClient(self.endpoint, **kwargs)
        self.assertEqual(u'fake-token', http_client_object.auth_token)
        self.assertTrue(http_client_object.identity_headers.
                        get('X-Auth-Token') is None)

    def test_identity_headers_and_no_token_in_session_header(self):
        # Tests that if token or X-Auth-Token are not provided in the kwargs
        # when creating the http client, the session headers don't contain
        # the X-Auth-Token key.
        identity_headers = {
            'X-User-Id': 'user',
            'X-Tenant-Id': 'tenant',
            'X-Roles': 'roles',
            'X-Identity-Status': 'Confirmed',
            'X-Service-Catalog': 'service_catalog',
        }
        kwargs = {'identity_headers': identity_headers}
        http_client_object = http.HTTPClient(self.endpoint, **kwargs)
        self.assertIsNone(http_client_object.auth_token)
        self.assertNotIn('X-Auth-Token', http_client_object.session.headers)

    def test_identity_headers_are_passed(self):
        # Tests that if token or X-Auth-Token are not provided in the kwargs
        # when creating the http client, the session headers don't contain
        # the X-Auth-Token key.
        identity_headers = {
            b'X-User-Id': b'user',
            b'X-Tenant-Id': b'tenant',
            b'X-Roles': b'roles',
            b'X-Identity-Status': b'Confirmed',
            b'X-Service-Catalog': b'service_catalog',
        }
        kwargs = {'identity_headers': identity_headers}
        http_client = http.HTTPClient(self.endpoint, **kwargs)

        def check_headers(*args, **kwargs):
            headers = kwargs.get('headers')
            for k, v in six.iteritems(identity_headers):
                self.assertEqual(v, headers[k])

            return utils.FakeResponse({}, six.StringIO('{}'))

        with mock.patch.object(http_client.session, 'request') as mreq:
            mreq.side_effect = check_headers
            http_client.get('http://example.com:9292/v1/images/my-image')

    def test_connection_refused(self):
        """
        Should receive a CommunicationError if connection refused.
        And the error should list the host and port that refused the
        connection
        """
        requests.Session.request(
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            data=mox.IgnoreArg(),
            headers=mox.IgnoreArg(),
            stream=mox.IgnoreArg(),
        ).AndRaise(requests.exceptions.ConnectionError())
        self.mock.ReplayAll()
        try:
            self.client.get('/v1/images/detail?limit=20')
            #NOTE(alaski) We expect exc.CommunicationError to be raised
            # so we should never reach this point.  try/except is used here
            # rather than assertRaises() so that we can check the body of
            # the exception.
            self.fail('An exception should have bypassed this line.')
        except glanceclient.exc.CommunicationError as comm_err:
            fail_msg = ("Exception message '%s' should contain '%s'" %
                       (comm_err.message, self.endpoint))
            self.assertTrue(self.endpoint in comm_err.message, fail_msg)

    def test_http_encoding(self):
        # Lets fake the response
        # returned by requests
        response = 'Ok'
        headers = {"Content-Type": "text/plain"}
        fake = utils.FakeResponse(headers, six.StringIO(response))
        requests.Session.request(
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            data=mox.IgnoreArg(),
            stream=mox.IgnoreArg(),
            headers=mox.IgnoreArg()).AndReturn(fake)
        self.mock.ReplayAll()

        headers = {"test": u'ni\xf1o'}
        resp, body = self.client.get('/v1/images/detail', headers=headers)
        self.assertEqual(fake, resp)

    def test_headers_encoding(self):
        value = u'ni\xf1o'
        headers = {"test": value, "none-val": None}
        encoded = self.client.encode_headers(headers)
        self.assertEqual(b"ni\xc3\xb1o", encoded[b"test"])
        self.assertNotIn("none-val", encoded)

    def test_raw_request(self):
        " Verify the path being used for HTTP requests reflects accurately. "
        headers = {"Content-Type": "text/plain"}
        response = 'Ok'
        fake = utils.FakeResponse({}, six.StringIO(response))
        requests.Session.request(
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            data=mox.IgnoreArg(),
            stream=mox.IgnoreArg(),
            headers=mox.IgnoreArg()).AndReturn(fake)
        self.mock.ReplayAll()

        resp, body = self.client.get('/v1/images/detail', headers=headers)
        self.assertEqual(fake, resp)

    def test_parse_endpoint(self):
        endpoint = 'http://example.com:9292'
        test_client = http.HTTPClient(endpoint, token=u'adc123')
        actual = test_client.parse_endpoint(endpoint)
        expected = parse.SplitResult(scheme='http',
                                     netloc='example.com:9292', path='',
                                     query='', fragment='')
        self.assertEqual(expected, actual)

    def test_get_connections_kwargs_http(self):
        endpoint = 'http://example.com:9292'
        test_client = http.HTTPClient(endpoint, token=u'adc123')
        self.assertEqual(test_client.timeout, 600.0)

    def test_http_chunked_request(self):
        # Lets fake the response
        # returned by requests
        response = "Ok"
        data = six.StringIO(response)
        fake = utils.FakeResponse({}, data)
        requests.Session.request(
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            stream=mox.IgnoreArg(),
            data=mox.IsA(types.GeneratorType),
            headers=mox.IgnoreArg()).AndReturn(fake)
        self.mock.ReplayAll()

        headers = {"test": u'chunked_request'}
        resp, body = self.client.post('/v1/images/',
                                      headers=headers, data=data)
        self.assertEqual(fake, resp)

    def test_http_json(self):
        data = {"test": "json_request"}
        fake = utils.FakeResponse({}, b"OK")

        def test_json(passed_data):
            """
            This function tests whether the data
            being passed to request's method is
            a valid json or not.

            This function will be called by pymox

            :params passed_data: The data being
                passed to requests.Session.request.
            """
            if not isinstance(passed_data, six.string_types):
                return False

            try:
                passed_data = json.loads(passed_data)
                return data == passed_data
            except (TypeError, ValueError):
                return False

        requests.Session.request(
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            stream=mox.IgnoreArg(),
            data=mox.Func(test_json),
            headers=mox.IgnoreArg()).AndReturn(fake)
        self.mock.ReplayAll()

        headers = {"test": u'chunked_request'}
        resp, body = self.client.post('/v1/images/',
                                      headers=headers,
                                      data=data)
        self.assertEqual(fake, resp)

    def test_http_chunked_response(self):
        headers = {"Content-Type": "application/octet-stream"}
        data = "TEST"
        fake = utils.FakeResponse(headers, six.StringIO(data))

        requests.Session.request(
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            stream=mox.IgnoreArg(),
            data=mox.IgnoreArg(),
            headers=mox.IgnoreArg()).AndReturn(fake)
        self.mock.ReplayAll()
        headers = {"test": u'chunked_request'}
        resp, body = self.client.get('/v1/images/')
        self.assertTrue(isinstance(body, types.GeneratorType))
        self.assertEqual([data], list(body))

    def test_log_http_response_with_non_ascii_char(self):
        try:
            response = 'Ok'
            headers = {"Content-Type": "text/plain",
                       "test": "value1\xa5\xa6"}
            fake = utils.FakeResponse(headers, six.StringIO(response))
            self.client.log_http_response(fake)
        except UnicodeDecodeError as e:
            self.fail("Unexpected UnicodeDecodeError exception '%s'" % e)


class TestVerifiedHTTPSConnection(testtools.TestCase):
    """Test fixture for glanceclient.common.http.VerifiedHTTPSConnection."""

    def test_setcontext_unable_to_load_cacert(self):
        """Add this UT case with Bug#1265730."""
        self.assertRaises(exc.SSLConfigurationError,
                          https.VerifiedHTTPSConnection,
                          "127.0.0.1",
                          None,
                          None,
                          None,
                          "gx_cacert",
                          None,
                          False,
                          True)
