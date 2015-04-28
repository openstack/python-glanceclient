# Copyright 2013 OpenStack Foundation
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

import sys

import six
import testtools

from glanceclient.common import progressbar
from glanceclient.tests import utils as test_utils


class TestProgressBarWrapper(testtools.TestCase):

    def test_iter_iterator_display_progress_bar(self):
        size = 100
        iterator = iter('X' * 100)
        saved_stdout = sys.stdout
        try:
            sys.stdout = output = test_utils.FakeTTYStdout()
            # Consume iterator.
            data = list(progressbar.VerboseIteratorWrapper(iterator, size))
            self.assertEqual(['X'] * 100, data)
            self.assertEqual(
                '[%s>] 100%%\n' % ('=' * 29),
                output.getvalue()
            )
        finally:
            sys.stdout = saved_stdout

    def test_iter_file_display_progress_bar(self):
        size = 98304
        file_obj = six.StringIO('X' * size)
        saved_stdout = sys.stdout
        try:
            sys.stdout = output = test_utils.FakeTTYStdout()
            file_obj = progressbar.VerboseFileWrapper(file_obj, size)
            chunksize = 1024
            chunk = file_obj.read(chunksize)
            while chunk:
                chunk = file_obj.read(chunksize)
            self.assertEqual(
                '[%s>] 100%%\n' % ('=' * 29),
                output.getvalue()
            )
        finally:
            sys.stdout = saved_stdout

    def test_iter_file_no_tty(self):
        size = 98304
        file_obj = six.StringIO('X' * size)
        saved_stdout = sys.stdout
        try:
            sys.stdout = output = test_utils.FakeNoTTYStdout()
            file_obj = progressbar.VerboseFileWrapper(file_obj, size)
            chunksize = 1024
            chunk = file_obj.read(chunksize)
            while chunk:
                chunk = file_obj.read(chunksize)
            # If stdout is not a tty progress bar should do nothing.
            self.assertEqual('', output.getvalue())
        finally:
            sys.stdout = saved_stdout
