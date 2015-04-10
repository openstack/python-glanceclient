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

from OpenSSL import crypto
from OpenSSL import SSL
try:
    from requests.packages.urllib3 import poolmanager
except ImportError:
    from urllib3 import poolmanager
import six
import ssl
import testtools
import threading

from glanceclient.common import http
from glanceclient.common import https

from glanceclient import Client
from glanceclient import exc

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
    """Check 'requests' based ssl verification occurs

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

    def _skip_python3(self):
        if six.PY3:
            msg = ("Skipping: python3 for now. Requires bugfix.")
            self.skipTest(msg)

    def test_v1_requests_cert_verification(self):
        """v1 regression test for bug 115260."""
        port = self.port
        url = 'https://0.0.0.0:%d' % port

        try:
            client = Client('1', url,
                            insecure=False,
                            ssl_compression=True)
            client.images.get('image123')
            self.fail('No SSL exception raised')
        except exc.CommunicationError as e:
            if 'certificate verify failed' not in e.message:
                self.fail('No certificate failure message received')
        except Exception as e:
            self.fail('Unexpected exception raised')

    def test_v1_requests_cert_verification_no_compression(self):
        """v1 regression test for bug 115260."""
        self._skip_python3()
        port = self.port
        url = 'https://0.0.0.0:%d' % port

        try:
            client = Client('1', url,
                            insecure=False,
                            ssl_compression=False)
            client.images.get('image123')
            self.fail('No SSL exception raised')
        except SSL.Error as e:
            if 'certificate verify failed' not in str(e):
                self.fail('No certificate failure message received')
        except Exception as e:
            self.fail('Unexpected exception raised')

    def test_v2_requests_cert_verification(self):
        """v2 regression test for bug 115260."""
        port = self.port
        url = 'https://0.0.0.0:%d' % port

        try:
            gc = Client('2', url,
                        insecure=False,
                        ssl_compression=True)
            gc.images.get('image123')
            self.fail('No SSL exception raised')
        except exc.CommunicationError as e:
            if 'certificate verify failed' not in e.message:
                self.fail('No certificate failure message received')
        except Exception as e:
            self.fail('Unexpected exception raised')

    def test_v2_requests_cert_verification_no_compression(self):
        """v2 regression test for bug 115260."""
        self._skip_python3()
        port = self.port
        url = 'https://0.0.0.0:%d' % port

        try:
            gc = Client('2', url,
                        insecure=False,
                        ssl_compression=False)
            gc.images.get('image123')
            self.fail('No SSL exception raised')
        except SSL.Error as e:
            if 'certificate verify failed' not in str(e):
                self.fail('No certificate failure message received')
        except Exception as e:
            self.fail('Unexpected exception raised')


class TestVerifiedHTTPSConnection(testtools.TestCase):
    def test_ssl_init_ok(self):
        """
        Test VerifiedHTTPSConnection class init
        """
        key_file = os.path.join(TEST_VAR_DIR, 'privatekey.key')
        cert_file = os.path.join(TEST_VAR_DIR, 'certificate.crt')
        cacert = os.path.join(TEST_VAR_DIR, 'ca.crt')
        try:
            https.VerifiedHTTPSConnection('127.0.0.1', 0,
                                          key_file=key_file,
                                          cert_file=cert_file,
                                          cacert=cacert)
        except exc.SSLConfigurationError:
            self.fail('Failed to init VerifiedHTTPSConnection.')

    def test_ssl_init_cert_no_key(self):
        """
        Test VerifiedHTTPSConnection: absence of SSL key file.
        """
        cert_file = os.path.join(TEST_VAR_DIR, 'certificate.crt')
        cacert = os.path.join(TEST_VAR_DIR, 'ca.crt')
        try:
            https.VerifiedHTTPSConnection('127.0.0.1', 0,
                                          cert_file=cert_file,
                                          cacert=cacert)
            self.fail('Failed to raise assertion.')
        except exc.SSLConfigurationError:
            pass

    def test_ssl_init_key_no_cert(self):
        """
        Test VerifiedHTTPSConnection: absence of SSL cert file.
        """
        key_file = os.path.join(TEST_VAR_DIR, 'privatekey.key')
        cacert = os.path.join(TEST_VAR_DIR, 'ca.crt')
        try:
            https.VerifiedHTTPSConnection('127.0.0.1', 0,
                                          key_file=key_file,
                                          cacert=cacert)
        except exc.SSLConfigurationError:
            pass
        except Exception:
            self.fail('Failed to init VerifiedHTTPSConnection.')

    def test_ssl_init_bad_key(self):
        """
        Test VerifiedHTTPSConnection: bad key.
        """
        cert_file = os.path.join(TEST_VAR_DIR, 'certificate.crt')
        cacert = os.path.join(TEST_VAR_DIR, 'ca.crt')
        key_file = os.path.join(TEST_VAR_DIR, 'badkey.key')
        try:
            https.VerifiedHTTPSConnection('127.0.0.1', 0,
                                          key_file=key_file,
                                          cert_file=cert_file,
                                          cacert=cacert)
            self.fail('Failed to raise assertion.')
        except exc.SSLConfigurationError:
            pass

    def test_ssl_init_bad_cert(self):
        """
        Test VerifiedHTTPSConnection: bad cert.
        """
        cert_file = os.path.join(TEST_VAR_DIR, 'badcert.crt')
        cacert = os.path.join(TEST_VAR_DIR, 'ca.crt')
        try:
            https.VerifiedHTTPSConnection('127.0.0.1', 0,
                                          cert_file=cert_file,
                                          cacert=cacert)
            self.fail('Failed to raise assertion.')
        except exc.SSLConfigurationError:
            pass

    def test_ssl_init_bad_ca(self):
        """
        Test VerifiedHTTPSConnection: bad CA.
        """
        cert_file = os.path.join(TEST_VAR_DIR, 'certificate.crt')
        cacert = os.path.join(TEST_VAR_DIR, 'badca.crt')
        try:
            https.VerifiedHTTPSConnection('127.0.0.1', 0,
                                          cert_file=cert_file,
                                          cacert=cacert)
            self.fail('Failed to raise assertion.')
        except exc.SSLConfigurationError:
            pass

    def test_ssl_cert_cname(self):
        """
        Test certificate: CN match
        """
        cert_file = os.path.join(TEST_VAR_DIR, 'certificate.crt')
        cert = crypto.load_certificate(crypto.FILETYPE_PEM,
                                       open(cert_file).read())
        # The expected cert should have CN=0.0.0.0
        self.assertEqual('0.0.0.0', cert.get_subject().commonName)
        try:
            conn = https.VerifiedHTTPSConnection('0.0.0.0', 0)
            https.do_verify_callback(None, cert, 0, 0, 1, host=conn.host)
        except Exception:
            self.fail('Unexpected exception.')

    def test_ssl_cert_cname_wildcard(self):
        """
        Test certificate: wildcard CN match
        """
        cert_file = os.path.join(TEST_VAR_DIR, 'wildcard-certificate.crt')
        cert = crypto.load_certificate(crypto.FILETYPE_PEM,
                                       open(cert_file).read())
        # The expected cert should have CN=*.pong.example.com
        self.assertEqual('*.pong.example.com', cert.get_subject().commonName)
        try:
            conn = https.VerifiedHTTPSConnection('ping.pong.example.com', 0)
            https.do_verify_callback(None, cert, 0, 0, 1, host=conn.host)
        except Exception:
            self.fail('Unexpected exception.')

    def test_ssl_cert_subject_alt_name(self):
        """
        Test certificate: SAN match
        """
        cert_file = os.path.join(TEST_VAR_DIR, 'certificate.crt')
        cert = crypto.load_certificate(crypto.FILETYPE_PEM,
                                       open(cert_file).read())
        # The expected cert should have CN=0.0.0.0
        self.assertEqual('0.0.0.0', cert.get_subject().commonName)
        try:
            conn = https.VerifiedHTTPSConnection('alt1.example.com', 0)
            https.do_verify_callback(None, cert, 0, 0, 1, host=conn.host)
        except Exception:
            self.fail('Unexpected exception.')

        try:
            conn = https.VerifiedHTTPSConnection('alt2.example.com', 0)
            https.do_verify_callback(None, cert, 0, 0, 1, host=conn.host)
        except Exception:
            self.fail('Unexpected exception.')

    def test_ssl_cert_subject_alt_name_wildcard(self):
        """
        Test certificate: wildcard SAN match
        """
        cert_file = os.path.join(TEST_VAR_DIR, 'wildcard-san-certificate.crt')
        cert = crypto.load_certificate(crypto.FILETYPE_PEM,
                                       open(cert_file).read())
        # The expected cert should have CN=0.0.0.0
        self.assertEqual('0.0.0.0', cert.get_subject().commonName)
        try:
            conn = https.VerifiedHTTPSConnection('alt1.example.com', 0)
            https.do_verify_callback(None, cert, 0, 0, 1, host=conn.host)
        except Exception:
            self.fail('Unexpected exception.')

        try:
            conn = https.VerifiedHTTPSConnection('alt2.example.com', 0)
            https.do_verify_callback(None, cert, 0, 0, 1, host=conn.host)
        except Exception:
            self.fail('Unexpected exception.')

        try:
            conn = https.VerifiedHTTPSConnection('alt3.example.net', 0)
            https.do_verify_callback(None, cert, 0, 0, 1, host=conn.host)
            self.fail('Failed to raise assertion.')
        except exc.SSLCertificateError:
            pass

    def test_ssl_cert_mismatch(self):
        """
        Test certificate: bogus host
        """
        cert_file = os.path.join(TEST_VAR_DIR, 'certificate.crt')
        cert = crypto.load_certificate(crypto.FILETYPE_PEM,
                                       open(cert_file).read())
        # The expected cert should have CN=0.0.0.0
        self.assertEqual('0.0.0.0', cert.get_subject().commonName)
        try:
            conn = https.VerifiedHTTPSConnection('mismatch.example.com', 0)
        except Exception:
            self.fail('Failed to init VerifiedHTTPSConnection.')

        self.assertRaises(exc.SSLCertificateError,
                          https.do_verify_callback, None, cert, 0, 0, 1,
                          host=conn.host)

    def test_ssl_expired_cert(self):
        """
        Test certificate: out of date cert
        """
        cert_file = os.path.join(TEST_VAR_DIR, 'expired-cert.crt')
        cert = crypto.load_certificate(crypto.FILETYPE_PEM,
                                       open(cert_file).read())
        # The expected expired cert has CN=openstack.example.com
        self.assertEqual('openstack.example.com',
                         cert.get_subject().commonName)
        try:
            conn = https.VerifiedHTTPSConnection('openstack.example.com', 0)
        except Exception:
            raise
            self.fail('Failed to init VerifiedHTTPSConnection.')
        self.assertRaises(exc.SSLCertificateError,
                          https.do_verify_callback, None, cert, 0, 0, 1,
                          host=conn.host)

    def test_ssl_broken_key_file(self):
        """
        Test verify exception is raised.
        """
        cert_file = os.path.join(TEST_VAR_DIR, 'certificate.crt')
        cacert = os.path.join(TEST_VAR_DIR, 'ca.crt')
        key_file = 'fake.key'
        self.assertRaises(
            exc.SSLConfigurationError,
            https.VerifiedHTTPSConnection, '127.0.0.1',
            0, key_file=key_file,
            cert_file=cert_file, cacert=cacert)

    def test_ssl_init_ok_with_insecure_true(self):
        """
        Test VerifiedHTTPSConnection class init
        """
        key_file = os.path.join(TEST_VAR_DIR, 'privatekey.key')
        cert_file = os.path.join(TEST_VAR_DIR, 'certificate.crt')
        cacert = os.path.join(TEST_VAR_DIR, 'ca.crt')
        try:
            https.VerifiedHTTPSConnection(
                '127.0.0.1', 0,
                key_file=key_file,
                cert_file=cert_file,
                cacert=cacert, insecure=True)
        except exc.SSLConfigurationError:
            self.fail('Failed to init VerifiedHTTPSConnection.')

    def test_ssl_init_ok_with_ssl_compression_false(self):
        """
        Test VerifiedHTTPSConnection class init
        """
        key_file = os.path.join(TEST_VAR_DIR, 'privatekey.key')
        cert_file = os.path.join(TEST_VAR_DIR, 'certificate.crt')
        cacert = os.path.join(TEST_VAR_DIR, 'ca.crt')
        try:
            https.VerifiedHTTPSConnection(
                '127.0.0.1', 0,
                key_file=key_file,
                cert_file=cert_file,
                cacert=cacert, ssl_compression=False)
        except exc.SSLConfigurationError:
            self.fail('Failed to init VerifiedHTTPSConnection.')

    def test_ssl_init_non_byte_string(self):
        """
        Test VerifiedHTTPSConnection class non byte string

        Reproduces bug #1301849
        """
        key_file = os.path.join(TEST_VAR_DIR, 'privatekey.key')
        cert_file = os.path.join(TEST_VAR_DIR, 'certificate.crt')
        cacert = os.path.join(TEST_VAR_DIR, 'ca.crt')
        # Note: we reproduce on python 2.6/2.7, on 3.3 the bug doesn't occur.
        key_file = key_file.encode('ascii', 'strict').decode('utf-8')
        cert_file = cert_file.encode('ascii', 'strict').decode('utf-8')
        cacert = cacert.encode('ascii', 'strict').decode('utf-8')
        try:
            https.VerifiedHTTPSConnection('127.0.0.1', 0,
                                          key_file=key_file,
                                          cert_file=cert_file,
                                          cacert=cacert)
        except exc.SSLConfigurationError:
            self.fail('Failed to init VerifiedHTTPSConnection.')


class TestRequestsIntegration(testtools.TestCase):

    def test_pool_patch(self):
        client = http.HTTPClient("https://localhost",
                                 ssl_compression=True)
        self.assertNotEqual(https.HTTPSConnectionPool,
                            poolmanager.pool_classes_by_scheme["https"])

        adapter = client.session.adapters.get("https://")
        self.assertFalse(isinstance(adapter, https.HTTPSAdapter))

        adapter = client.session.adapters.get("glance+https://")
        self.assertFalse(isinstance(adapter, https.HTTPSAdapter))

    def test_custom_https_adapter(self):
        client = http.HTTPClient("https://localhost",
                                 ssl_compression=False)
        self.assertNotEqual(https.HTTPSConnectionPool,
                            poolmanager.pool_classes_by_scheme["https"])

        adapter = client.session.adapters.get("https://")
        self.assertFalse(isinstance(adapter, https.HTTPSAdapter))

        adapter = client.session.adapters.get("glance+https://")
        self.assertTrue(isinstance(adapter, https.HTTPSAdapter))
