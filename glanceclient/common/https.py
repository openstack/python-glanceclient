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
import ssl
import struct

import OpenSSL


try:
    from eventlet import patcher
    # Handle case where we are running in a monkey patched environment
    if patcher.is_monkey_patched('socket'):
        from eventlet.green.httplib import HTTPSConnection
        from eventlet.green.OpenSSL.SSL import GreenConnection as Connection
    else:
        raise ImportError
except ImportError:
    import http.client
    from OpenSSL import SSL
    HTTPSConnection = http.client.HTTPSConnection
    Connection = SSL.Connection


from glanceclient import exc


def verify_callback(host=None):
    """Provide wrapper for do_verify_callback.

    We use a partial around the 'real' verify_callback function
    so that we can stash the host value without holding a
    reference on the VerifiedHTTPSConnection.
    """
    def wrapper(connection, x509, errnum,
                depth, preverify_ok, host=host):
        return do_verify_callback(connection, x509, errnum,
                                  depth, preverify_ok, host=host)
    return wrapper


def do_verify_callback(connection, x509, errnum,
                       depth, preverify_ok, host=None):
    """Verify the server's SSL certificate.

    This is a standalone function rather than a method to avoid
    issues around closing sockets if a reference is held on
    a VerifiedHTTPSConnection by the callback function.
    """
    if x509.has_expired():
        msg = "SSL Certificate expired on '%s'" % x509.get_notAfter()
        raise exc.SSLCertificateError(msg)

    if depth == 0 and preverify_ok:
        # We verify that the host matches against the last
        # certificate in the chain
        return host_matches_cert(host, x509)
    else:
        # Pass through OpenSSL's default result
        return preverify_ok


def host_matches_cert(host, x509):
    """Verify the certificate identifies the host.

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


def to_bytes(s):
    if isinstance(s, str):
        return bytes(s, 'latin-1')
    else:
        return s


class OpenSSLConnectionDelegator(object):
    """An OpenSSL.SSL.Connection delegator.

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
    """Extended OpenSSL HTTPSConnection for enhanced SSL support.

    Note: Much of this functionality can eventually be replaced
          with native Python 3.3 code.
    """
    # Restrict the set of client supported cipher suites
    CIPHERS = 'ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:'\
              'eCDH+AES128:DH+AES:ECDH+3DES:DH+3DES:RSA+AESGCM:'\
              'RSA+AES:RSA+3DES:!aNULL:!MD5:!DSS'

    def __init__(self, host, port=None, key_file=None, cert_file=None,
                 cacert=None, timeout=None, insecure=False,
                 ssl_compression=True):
        # List of exceptions reported by Python3 instead of
        # SSLConfigurationError
        excp_lst = (TypeError, FileNotFoundError, ssl.SSLError)
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

    def set_context(self):
        """Set up the OpenSSL context."""
        self.context = OpenSSL.SSL.Context(OpenSSL.SSL.SSLv23_METHOD)
        self.context.set_cipher_list(self.CIPHERS)

        if self.ssl_compression is False:
            self.context.set_options(0x20000)  # SSL_OP_NO_COMPRESSION

        if self.insecure is not True:
            self.context.set_verify(OpenSSL.SSL.VERIFY_PEER,
                                    verify_callback(host=self.host))
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
        """Connect to an SSL port using the OpenSSL library.

        This method also applies per-connection parameters to the connection.
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
