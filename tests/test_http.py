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
    def test_connection_refused(self):
        """
        Should receive a CommunicationError if connection refused.
        And the error should list the host and port that refused the
        connection
        """
        endpoint = 'http://example.com:9292'
        client = http.HTTPClient(endpoint, token=u'abc123')
        m = mox.Mox()
        m.StubOutWithMock(httplib.HTTPConnection, 'request')
        httplib.HTTPConnection.request(
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            headers=mox.IgnoreArg(),
        ).AndRaise(socket.error())
        m.ReplayAll()
        try:
            client.json_request('GET', '/v1/images/detail?limit=20')
            #NOTE(alaski) We expect exc.CommunicationError to be raised
            # so we should never reach this point.  try/except is used here
            # rather than assertRaises() so that we can check the body of
            # the exception.
            self.fail('An exception should have bypassed this line.')
        except exc.CommunicationError, comm_err:
            fail_msg = ("Exception message '%s' should contain '%s'" %
                       (comm_err.message, endpoint))
            self.assertTrue(endpoint in comm_err.message, fail_msg)
        finally:
            m.UnsetStubs()


class TestResponseBodyIterator(testtools.TestCase):
    def test_iter_default_chunk_size_64k(self):
        resp = utils.FakeResponse({}, StringIO.StringIO('X' * 98304))
        iterator = http.ResponseBodyIterator(resp)
        chunks = list(iterator)
        self.assertEqual(chunks, ['X' * 65536, 'X' * 32768])
