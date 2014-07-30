# Copyright 2014 Red Hat, Inc
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

import socket
import struct

import OpenSSL
from requests import adapters
try:
    from requests.packages.urllib3 import connectionpool
    from requests.packages.urllib3 import poolmanager
except ImportError:
    from urllib3 import connectionpool
    from urllib3 import poolmanager

import six
import ssl

from glanceclient.common import utils

try:
    from eventlet import patcher
    # Handle case where we are running in a monkey patched environment
    if patcher.is_monkey_patched('socket'):
        from eventlet.green.httplib import HTTPSConnection
        from eventlet.green.OpenSSL.SSL import GreenConnection as Connection
        from eventlet.greenio import GreenSocket
        # TODO(mclaren): A getsockopt workaround: see 'getsockopt' doc string
        GreenSocket.getsockopt = utils.getsockopt
    else:
        raise ImportError
except ImportError:
    try:
        from httplib import HTTPSConnection
    except ImportError:
        from http.client import HTTPSConnection
    from OpenSSL.SSL import Connection as Connection


from glanceclient import exc
from glanceclient.openstack.common import strutils


def to_bytes(s):
    if isinstance(s, six.string_types):
        return six.b(s)
    else:
        return s


class HTTPSAdapter(adapters.HTTPAdapter):
    """
    This adapter will be used just when
    ssl compression should be disabled.

    The init method overwrites the default
    https pool by setting glanceclient's
    one.
    """

    def __init__(self, *args, **kwargs):
        # NOTE(flaper87): This line forces poolmanager to use
        # glanceclient HTTPSConnection
        classes_by_scheme = poolmanager.pool_classes_by_scheme
        classes_by_scheme["glance+https"] = HTTPSConnectionPool
        super(HTTPSAdapter, self).__init__(*args, **kwargs)

    def request_url(self, request, proxies):
        # NOTE(flaper87): Make sure the url is encoded, otherwise
        # python's standard httplib will fail with a TypeError.
        url = super(HTTPSAdapter, self).request_url(request, proxies)
        return strutils.safe_encode(url)

    def cert_verify(self, conn, url, verify, cert):
        super(HTTPSAdapter, self).cert_verify(conn, url, verify, cert)
        conn.ca_certs = verify[0]
        conn.insecure = verify[1]


class HTTPSConnectionPool(connectionpool.HTTPSConnectionPool):
    """
    HTTPSConnectionPool will be instantiated when a new
    connection is requested to the HTTPSAdapter.This
    implementation overwrites the _new_conn method and
    returns an instances of glanceclient's VerifiedHTTPSConnection
    which handles no compression.

    ssl_compression is hard-coded to False because this will
    be used just when the user sets --no-ssl-compression.
    """

    scheme = 'glance+https'

    def _new_conn(self):
        self.num_connections += 1
        return VerifiedHTTPSConnection(host=self.host,
                                       port=self.port,
                                       key_file=self.key_file,
                                       cert_file=self.cert_file,
                                       cacert=self.ca_certs,
                                       insecure=self.insecure,
                                       ssl_compression=False)


class OpenSSLConnectionDelegator(object):
    """
    An OpenSSL.SSL.Connection delegator.

    Supplies an additional 'makefile' method which httplib requires
    and is not present in OpenSSL.SSL.Connection.

    Note: Since it is not possible to inherit from OpenSSL.SSL.Connection
    a delegator must be used.
    """
    def __init__(self, *args, **kwargs):
        self.connection = Connection(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.connection, name)

    def makefile(self, *args, **kwargs):
        return socket._fileobject(self.connection, *args, **kwargs)


class VerifiedHTTPSConnection(HTTPSConnection):
    """
    Extended HTTPSConnection which uses the OpenSSL library
    for enhanced SSL support.
    Note: Much of this functionality can eventually be replaced
          with native Python 3.3 code.
    """
    def __init__(self, host, port=None, key_file=None, cert_file=None,
                 cacert=None, timeout=None, insecure=False,
                 ssl_compression=True):
        # List of exceptions reported by Python3 instead of
        # SSLConfigurationError
        if six.PY3:
            excp_lst = (TypeError, FileNotFoundError, ssl.SSLError)
        else:
            excp_lst = ()
        try:
            HTTPSConnection.__init__(self, host, port,
                                     key_file=key_file,
                                     cert_file=cert_file)
            self.key_file = key_file
            self.cert_file = cert_file
            self.timeout = timeout
            self.insecure = insecure
            # NOTE(flaper87): `is_verified` is needed for
            # requests' urllib3. If insecure is True then
            # the request is not `verified`, hence `not insecure`
            self.is_verified = not insecure
            self.ssl_compression = ssl_compression
            self.cacert = None if cacert is None else str(cacert)
            self.set_context()
            # ssl exceptions are reported in various form in Python 3
            # so to be compatible, we report the same kind as under
            # Python2
        except excp_lst as e:
            raise exc.SSLConfigurationError(str(e))

    @staticmethod
    def host_matches_cert(host, x509):
        """
        Verify that the x509 certificate we have received
        from 'host' correctly identifies the server we are
        connecting to, ie that the certificate's Common Name
        or a Subject Alternative Name matches 'host'.
        """
        def check_match(name):
            # Directly match the name
            if name == host:
                return True

            # Support single wildcard matching
            if name.startswith('*.') and host.find('.') > 0:
                if name[2:] == host.split('.', 1)[1]:
                    return True

        common_name = x509.get_subject().commonName

        # First see if we can match the CN
        if check_match(common_name):
            return True
            # Also try Subject Alternative Names for a match
        san_list = None
        for i in range(x509.get_extension_count()):
            ext = x509.get_extension(i)
            if ext.get_short_name() == b'subjectAltName':
                san_list = str(ext)
                for san in ''.join(san_list.split()).split(','):
                    if san.startswith('DNS:'):
                        if check_match(san.split(':', 1)[1]):
                            return True

        # Server certificate does not match host
        msg = ('Host "%s" does not match x509 certificate contents: '
               'CommonName "%s"' % (host, common_name))
        if san_list is not None:
            msg = msg + ', subjectAltName "%s"' % san_list
        raise exc.SSLCertificateError(msg)

    def verify_callback(self, connection, x509, errnum,
                        depth, preverify_ok):
        if x509.has_expired():
            msg = "SSL Certificate expired on '%s'" % x509.get_notAfter()
            raise exc.SSLCertificateError(msg)

        if depth == 0 and preverify_ok:
            # We verify that the host matches against the last
            # certificate in the chain
            return self.host_matches_cert(self.host, x509)
        else:
            # Pass through OpenSSL's default result
            return preverify_ok

    def set_context(self):
        """
        Set up the OpenSSL context.
        """
        self.context = OpenSSL.SSL.Context(OpenSSL.SSL.SSLv23_METHOD)

        if self.ssl_compression is False:
            self.context.set_options(0x20000)  # SSL_OP_NO_COMPRESSION

        if self.insecure is not True:
            self.context.set_verify(OpenSSL.SSL.VERIFY_PEER,
                                    self.verify_callback)
        else:
            self.context.set_verify(OpenSSL.SSL.VERIFY_NONE,
                                    lambda *args: True)

        if self.cert_file:
            try:
                self.context.use_certificate_file(self.cert_file)
            except Exception as e:
                msg = 'Unable to load cert from "%s" %s' % (self.cert_file, e)
                raise exc.SSLConfigurationError(msg)
            if self.key_file is None:
                # We support having key and cert in same file
                try:
                    self.context.use_privatekey_file(self.cert_file)
                except Exception as e:
                    msg = ('No key file specified and unable to load key '
                           'from "%s" %s' % (self.cert_file, e))
                    raise exc.SSLConfigurationError(msg)

        if self.key_file:
            try:
                self.context.use_privatekey_file(self.key_file)
            except Exception as e:
                msg = 'Unable to load key from "%s" %s' % (self.key_file, e)
                raise exc.SSLConfigurationError(msg)

        if self.cacert:
            try:
                self.context.load_verify_locations(to_bytes(self.cacert))
            except Exception as e:
                msg = 'Unable to load CA from "%s" %s' % (self.cacert, e)
                raise exc.SSLConfigurationError(msg)
        else:
            self.context.set_default_verify_paths()

    def connect(self):
        """
        Connect to an SSL port using the OpenSSL library and apply
        per-connection parameters.
        """
        result = socket.getaddrinfo(self.host, self.port, 0,
                                    socket.SOCK_STREAM)
        if result:
            socket_family = result[0][0]
            if socket_family == socket.AF_INET6:
                sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            # If due to some reason the address lookup fails - we still connect
            # to IPv4 socket. This retains the older behavior.
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.timeout is not None:
            # '0' microseconds
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO,
                            struct.pack('LL', self.timeout, 0))
        self.sock = OpenSSLConnectionDelegator(self.context, sock)
        self.sock.connect((self.host, self.port))
