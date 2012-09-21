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

import os
import unittest

from glanceclient import exc
from glanceclient.common import http

TEST_VAR_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                            'var'))


class TestVerifiedHTTPSConnection(unittest.TestCase):
    def test_ssl_init_ok(self):
        """
        Test VerifiedHTTPSConnection class init
        """
        key_file = os.path.join(TEST_VAR_DIR, 'privatekey.key')
        cert_file = os.path.join(TEST_VAR_DIR, 'certificate.crt')
        ca_file = os.path.join(TEST_VAR_DIR, 'ca.crt')
        try:
            conn = http.VerifiedHTTPSConnection('127.0.0.1', 0,
                                                key_file=key_file,
                                                cert_file=cert_file,
                                                ca_file=ca_file)
        except exc.SSLConfigurationError:
            self.fail('Failed to init VerifiedHTTPSConnection.')

    def test_ssl_init_cert_no_key(self):
        """
        Test VerifiedHTTPSConnection: absense of SSL key file.
        """
        cert_file = os.path.join(TEST_VAR_DIR, 'certificate.crt')
        ca_file = os.path.join(TEST_VAR_DIR, 'ca.crt')
        try:
            conn = http.VerifiedHTTPSConnection('127.0.0.1', 0,
                                                cert_file=cert_file,
                                                ca_file=ca_file)
            self.fail('Failed to raise assertion.')
        except exc.SSLConfigurationError:
            pass

    def test_ssl_init_key_no_cert(self):
        """
        Test VerifiedHTTPSConnection: absense of SSL cert file.
        """
        key_file = os.path.join(TEST_VAR_DIR, 'privatekey.key')
        ca_file = os.path.join(TEST_VAR_DIR, 'ca.crt')
        try:
            conn = http.VerifiedHTTPSConnection('127.0.0.1', 0,
                                                key_file=key_file,
                                                ca_file=ca_file)
        except:
            self.fail('Failed to init VerifiedHTTPSConnection.')

    def test_ssl_init_bad_key(self):
        """
        Test VerifiedHTTPSConnection: bad key.
        """
        key_file = os.path.join(TEST_VAR_DIR, 'badkey.key')
        cert_file = os.path.join(TEST_VAR_DIR, 'certificate.crt')
        ca_file = os.path.join(TEST_VAR_DIR, 'ca.crt')
        try:
            conn = http.VerifiedHTTPSConnection('127.0.0.1', 0,
                                                cert_file=cert_file,
                                                ca_file=ca_file)
            self.fail('Failed to raise assertion.')
        except exc.SSLConfigurationError:
            pass

    def test_ssl_init_bad_cert(self):
        """
        Test VerifiedHTTPSConnection: bad cert.
        """
        key_file = os.path.join(TEST_VAR_DIR, 'privatekey.key')
        cert_file = os.path.join(TEST_VAR_DIR, 'badcert.crt')
        ca_file = os.path.join(TEST_VAR_DIR, 'ca.crt')
        try:
            conn = http.VerifiedHTTPSConnection('127.0.0.1', 0,
                                                cert_file=cert_file,
                                                ca_file=ca_file)
            self.fail('Failed to raise assertion.')
        except exc.SSLConfigurationError:
            pass

    def test_ssl_init_bad_ca(self):
        """
        Test VerifiedHTTPSConnection: bad CA.
        """
        key_file = os.path.join(TEST_VAR_DIR, 'privatekey.key')
        cert_file = os.path.join(TEST_VAR_DIR, 'certificate.crt')
        ca_file = os.path.join(TEST_VAR_DIR, 'badca.crt')
        try:
            conn = http.VerifiedHTTPSConnection('127.0.0.1', 0,
                                                cert_file=cert_file,
                                                ca_file=ca_file)
            self.fail('Failed to raise assertion.')
        except exc.SSLConfigurationError:
            pass
