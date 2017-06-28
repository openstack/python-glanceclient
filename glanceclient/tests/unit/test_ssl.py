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

import os

import mock
import six
import ssl
import testtools
import threading

from glanceclient import Client
from glanceclient import exc
from glanceclient import v1
from glanceclient import v2

if six.PY3 is True:
    import socketserver
else:
    import SocketServer as socketserver


TEST_VAR_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                            'var'))


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.recv(1024)
        response = b'somebytes'
        self.request.sendall(response)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    def get_request(self):
        key_file = os.path.join(TEST_VAR_DIR, 'privatekey.key')
        cert_file = os.path.join(TEST_VAR_DIR, 'certificate.crt')
        cacert = os.path.join(TEST_VAR_DIR, 'ca.crt')
        (_sock, addr) = socketserver.TCPServer.get_request(self)
        sock = ssl.wrap_socket(_sock,
                               certfile=cert_file,
                               keyfile=key_file,
                               ca_certs=cacert,
                               server_side=True,
                               cert_reqs=ssl.CERT_REQUIRED)
        return sock, addr


class TestHTTPSVerifyCert(testtools.TestCase):
    """Check 'requests' based ssl verification occurs.

    The requests library performs SSL certificate validation,
    however there is still a need to check that the glance
    client is properly integrated with requests so that
    cert validation actually happens.
    """
    def setUp(self):
        # Rather than spinning up a new process, we create
        # a thread to perform client/server interaction.
        # This should run more quickly.
        super(TestHTTPSVerifyCert, self).setUp()
        server = ThreadedTCPServer(('127.0.0.1', 0),
                                   ThreadedTCPRequestHandler)
        __, self.port = server.server_address
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

    @mock.patch('sys.stderr')
    def test_v1_requests_cert_verification(self, __):
        """v1 regression test for bug 115260."""
        port = self.port
        url = 'https://0.0.0.0:%d' % port

        try:
            client = v1.Client(url,
                               insecure=False,
                               ssl_compression=True)
            client.images.get('image123')
            self.fail('No SSL exception has been raised')
        except exc.CommunicationError as e:
            if 'certificate verify failed' not in e.message:
                self.fail('No certificate failure message is received')

    @mock.patch('sys.stderr')
    def test_v1_requests_cert_verification_no_compression(self, __):
        """v1 regression test for bug 115260."""
        # Legacy test. Verify 'no compression' has no effect
        port = self.port
        url = 'https://0.0.0.0:%d' % port

        try:
            client = v1.Client(url,
                               insecure=False,
                               ssl_compression=False)
            client.images.get('image123')
            self.fail('No SSL exception has been raised')
        except exc.CommunicationError as e:
            if 'certificate verify failed' not in e.message:
                self.fail('No certificate failure message is received')

    @mock.patch('sys.stderr')
    def test_v2_requests_cert_verification(self, __):
        """v2 regression test for bug 115260."""
        port = self.port
        url = 'https://0.0.0.0:%d' % port

        try:
            gc = v2.Client(url,
                           insecure=False,
                           ssl_compression=True)
            gc.images.get('image123')
            self.fail('No SSL exception has been raised')
        except exc.CommunicationError as e:
            if 'certificate verify failed' not in e.message:
                self.fail('No certificate failure message is received')

    @mock.patch('sys.stderr')
    def test_v2_requests_cert_verification_no_compression(self, __):
        """v2 regression test for bug 115260."""
        # Legacy test. Verify 'no compression' has no effect
        port = self.port
        url = 'https://0.0.0.0:%d' % port

        try:
            gc = v2.Client(url,
                           insecure=False,
                           ssl_compression=False)
            gc.images.get('image123')
            self.fail('No SSL exception has been raised')
        except exc.CommunicationError as e:
            if 'certificate verify failed' not in e.message:
                self.fail('No certificate failure message is received')

    @mock.patch('sys.stderr')
    def test_v2_requests_valid_cert_verification(self, __):
        """Test absence of SSL key file."""
        port = self.port
        url = 'https://0.0.0.0:%d' % port
        cacert = os.path.join(TEST_VAR_DIR, 'ca.crt')

        try:
            gc = Client('2', url,
                        insecure=False,
                        ssl_compression=True,
                        cacert=cacert)
            gc.images.get('image123')
        except exc.CommunicationError as e:
            if 'certificate verify failed' in e.message:
                self.fail('Certificate failure message is received')

    @mock.patch('sys.stderr')
    def test_v2_requests_valid_cert_verification_no_compression(self, __):
        """Test VerifiedHTTPSConnection: absence of SSL key file."""
        port = self.port
        url = 'https://0.0.0.0:%d' % port
        cacert = os.path.join(TEST_VAR_DIR, 'ca.crt')

        try:
            gc = Client('2', url,
                        insecure=False,
                        ssl_compression=False,
                        cacert=cacert)
            gc.images.get('image123')
        except exc.CommunicationError as e:
            if 'certificate verify failed' in e.message:
                self.fail('Certificate failure message is received')

    @mock.patch('sys.stderr')
    def test_v2_requests_valid_cert_no_key(self, __):
        """Test VerifiedHTTPSConnection: absence of SSL key file."""
        port = self.port
        url = 'https://0.0.0.0:%d' % port
        cert_file = os.path.join(TEST_VAR_DIR, 'certificate.crt')
        cacert = os.path.join(TEST_VAR_DIR, 'ca.crt')

        try:
            gc = Client('2', url,
                        insecure=False,
                        ssl_compression=False,
                        cert_file=cert_file,
                        cacert=cacert)
            gc.images.get('image123')
        except exc.CommunicationError as e:
            if ('PEM lib' not in e.message):
                self.fail('No appropriate failure message is received')

    @mock.patch('sys.stderr')
    def test_v2_requests_bad_cert(self, __):
        """Test VerifiedHTTPSConnection: absence of SSL key file."""
        port = self.port
        url = 'https://0.0.0.0:%d' % port
        cert_file = os.path.join(TEST_VAR_DIR, 'badcert.crt')
        cacert = os.path.join(TEST_VAR_DIR, 'ca.crt')

        try:
            gc = Client('2', url,
                        insecure=False,
                        ssl_compression=False,
                        cert_file=cert_file,
                        cacert=cacert)
            gc.images.get('image123')
        except exc.CommunicationError as e:
            # NOTE(dsariel)
            # starting from python 2.7.8 the way to handle loading private
            # keys into the SSL_CTX was changed and error message become
            # similar to the one in 3.X
            if (six.PY2 and 'PrivateKey' not in e.message and
                    'PEM lib' not in e.message or
                    six.PY3 and 'PEM lib' not in e.message):
                self.fail('No appropriate failure message is received')

    @mock.patch('sys.stderr')
    def test_v2_requests_bad_ca(self, __):
        """Test VerifiedHTTPSConnection: absence of SSL key file."""
        port = self.port
        url = 'https://0.0.0.0:%d' % port
        cacert = os.path.join(TEST_VAR_DIR, 'badca.crt')

        try:
            gc = Client('2', url,
                        insecure=False,
                        ssl_compression=False,
                        cacert=cacert)
            gc.images.get('image123')
        except exc.CommunicationError as e:
            if 'invalid path' not in e.message:
                raise
