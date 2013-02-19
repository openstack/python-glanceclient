# Copyright 2012 OpenStack LLC.
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

import httplib
import socket
import StringIO
import testtools

import mox

from glanceclient import exc
from glanceclient.common import http
from tests import utils


class TestClient(testtools.TestCase):

    def setUp(self):
        super(TestClient, self).setUp()
        self.mock = mox.Mox()
        self.mock.StubOutWithMock(httplib.HTTPConnection, 'request')
        self.mock.StubOutWithMock(httplib.HTTPConnection, 'getresponse')

        self.endpoint = 'http://example.com:9292'
        self.client = http.HTTPClient(self.endpoint, token=u'abc123')

    def tearDown(self):
        super(TestClient, self).tearDown()
        self.mock.UnsetStubs()

    def test_connection_refused(self):
        """
        Should receive a CommunicationError if connection refused.
        And the error should list the host and port that refused the
        connection
        """
        httplib.HTTPConnection.request(
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            headers=mox.IgnoreArg(),
        ).AndRaise(socket.error())
        self.mock.ReplayAll()
        try:
            self.client.json_request('GET', '/v1/images/detail?limit=20')
            #NOTE(alaski) We expect exc.CommunicationError to be raised
            # so we should never reach this point.  try/except is used here
            # rather than assertRaises() so that we can check the body of
            # the exception.
            self.fail('An exception should have bypassed this line.')
        except exc.CommunicationError, comm_err:
            fail_msg = ("Exception message '%s' should contain '%s'" %
                       (comm_err.message, self.endpoint))
            self.assertTrue(self.endpoint in comm_err.message, fail_msg)

    def test_http_encoding(self):
        httplib.HTTPConnection.request(
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            headers=mox.IgnoreArg())

        # Lets fake the response
        # returned by httplib
        expected_response = 'Ok'
        fake = utils.FakeResponse({}, StringIO.StringIO(expected_response))
        httplib.HTTPConnection.getresponse().AndReturn(fake)
        self.mock.ReplayAll()

        headers = {"test": u'ni\xf1o'}
        resp, body = self.client.raw_request('GET', '/v1/images/detail',
                                                    headers=headers)
        self.assertEqual(resp, fake)


class TestHostResolutionError(testtools.TestCase):

    def setUp(self):
        super(TestHostResolutionError, self).setUp()
        self.mock = mox.Mox()
        self.invalid_host = "example.com.incorrect_top_level_domain"

    def test_incorrect_domain_error(self):
        """
        Make sure that using a domain which does not resolve causes an
        exception which mentions that specific hostname as a reason for
        failure.
        """
        class FailingConnectionClass(object):
            def __init__(self, *args, **kwargs):
                pass

            def putrequest(self, *args, **kwargs):
                raise socket.gaierror(-2, "Name or service not known")

            def request(self, *args, **kwargs):
                raise socket.gaierror(-2, "Name or service not known")

        self.endpoint = 'http://%s:9292' % (self.invalid_host,)
        self.client = http.HTTPClient(self.endpoint, token=u'abc123')

        self.mock.StubOutWithMock(self.client, 'get_connection')
        self.client.get_connection().AndReturn(FailingConnectionClass())
        self.mock.ReplayAll()

        try:
            self.client.raw_request('GET', '/example/path')
            self.fail("gaierror should be raised")
        except exc.InvalidEndpoint as e:
            self.assertTrue(self.invalid_host in str(e),
                            "exception should contain the hostname")

    def tearDown(self):
        super(TestHostResolutionError, self).tearDown()
        self.mock.UnsetStubs()


class TestResponseBodyIterator(testtools.TestCase):
    def test_iter_default_chunk_size_64k(self):
        resp = utils.FakeResponse({}, StringIO.StringIO('X' * 98304))
        iterator = http.ResponseBodyIterator(resp)
        chunks = list(iterator)
        self.assertEqual(chunks, ['X' * 65536, 'X' * 32768])
