# Copyright 2022 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import testtools
from unittest import mock

from glanceclient.v2 import info


class TestController(testtools.TestCase):
    def setUp(self):
        super(TestController, self).setUp()
        self.fake_client = mock.MagicMock()
        self.info_controller = info.Controller(self.fake_client, None)

    def test_get_usage(self):
        fake_usage = {
            'usage': {
                'quota1': {'limit': 10, 'usage': 0},
                'quota2': {'limit': 20, 'usage': 5},
            }
        }
        self.fake_client.get.return_value = (mock.MagicMock(), fake_usage)
        usage = self.info_controller.get_usage()
        self.assertEqual(fake_usage['usage'], usage)
        self.fake_client.get.assert_called_once_with('/v2/info/usage')
