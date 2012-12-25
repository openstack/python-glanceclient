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

import errno
import testtools

from glanceclient.common import utils


class TestUtils(testtools.TestCase):

    def test_integrity_iter_without_checksum(self):
        try:
            data = ''.join([f for f in utils.integrity_iter('A', None)])
            self.fail('integrity checked passed without checksum.')
        except IOError, e:
            self.assertEqual(errno.EPIPE, e.errno)
            msg = 'was 7fc56270e7a70fa81a5935b72eacbe29 expected None'
            self.assertTrue(msg in str(e))

    def test_integrity_iter_with_wrong_checksum(self):
        try:
            data = ''.join([f for f in utils.integrity_iter('BB', 'wrong')])
            self.fail('integrity checked passed with wrong checksum')
        except IOError, e:
            self.assertEqual(errno.EPIPE, e.errno)
            msg = 'was 9d3d9048db16a7eee539e93e3618cbe7 expected wrong'
            self.assertTrue('expected wrong' in str(e))

    def test_integrity_iter_with_checksum(self):
        fixture = 'CCC'
        checksum = 'defb99e69a9f1f6e06f15006b1f166ae'
        data = ''.join([f for f in utils.integrity_iter(fixture, checksum)])

    def test_make_size_human_readable(self):
        self.assertEqual("106B", utils.make_size_human_readable(106))
        self.assertEqual("1000kB", utils.make_size_human_readable(1024000))
        self.assertEqual("1MB", utils.make_size_human_readable(1048576))
        self.assertEqual("1.4GB", utils.make_size_human_readable(1476395008))
        self.assertEqual("9.3MB", utils.make_size_human_readable(9761280))
