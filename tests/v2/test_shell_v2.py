# Copyright 2013 OpenStack LLC.
# Copyright (C) 2013 Yahoo! Inc.
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
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import mock
import testtools

from glanceclient import client
from glanceclient.common import utils
from glanceclient.v2 import shell as test_shell


class LegacyShellV1Test(testtools.TestCase):
    def test_do_image_list(self):
        gc = client.Client('1', 'http://no.where')

        class Fake():
            def __init__(self):
                self.page_size = 18
                self.visibility = True
                self.member_status = 'Fake'
                self.owner = 'test'
                self.checksum = 'fake_checksum'

        with mock.patch.object(gc.images, 'list') as mocked_list:
            mocked_list.return_value = {}
            actual = test_shell.do_image_list(gc, Fake())

    def test_do_image_show(self):
        gc = client.Client('1', 'http://no.where')

        class Fake():
            def __init__(self):
                self.page_size = 18
                self.id = 'pass'

        with mock.patch.object(gc.images, 'get') as mocked_list:
            mocked_list.return_value = {}
            actual = test_shell.do_image_show(gc, Fake())

    def test_do_explain(self):
        my_mocked_gc = mock.Mock()
        my_mocked_gc.schemas.return_value = 'test'
        my_mocked_gc.get.return_value = {}

        class Fake():
            def __init__(self):
                self.page_size = 18
                self.id = 'pass'
                self.schemas = 'test'
                self.model = 'test'

        with mock.patch.object(utils, 'print_list'):
            test_shell.do_explain(my_mocked_gc, Fake())

    def test_image_download(self):
        class Fake():
            id = 'pass'
            file = 'test'

        gc = client.Client('1', 'http://no.where')
        with mock.patch.object(gc.images, 'data') as mocked_data:
            mocked_data.return_value = 'test_passed'
            test_shell.do_image_download(gc, Fake())

    def test_do_image_delete(self):
        class Fake():
            id = 'pass'
            file = 'test'

        gc = client.Client('1', 'http://no.where')
        with mock.patch.object(gc.images, 'delete') as mocked_delete:
            mocked_delete.return_value = 0
            test_shell.do_image_delete(gc, Fake())
