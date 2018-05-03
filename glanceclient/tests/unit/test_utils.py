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

import sys

import mock
from oslo_utils import encodeutils
from requests import Response
import six
# NOTE(jokke): simplified transition to py3, behaves like py2 xrange
from six.moves import range
import testtools

from glanceclient.common import utils


REQUEST_ID = 'req-1234'


def create_response_obj_with_req_id(req_id):
    resp = Response()
    resp.headers['x-openstack-request-id'] = req_id
    return resp


class TestUtils(testtools.TestCase):

    def test_make_size_human_readable(self):
        self.assertEqual("106B", utils.make_size_human_readable(106))
        self.assertEqual("1000kB", utils.make_size_human_readable(1024000))
        self.assertEqual("1MB", utils.make_size_human_readable(1048576))
        self.assertEqual("1.4GB", utils.make_size_human_readable(1476395008))
        self.assertEqual("9.3MB", utils.make_size_human_readable(9761280))
        self.assertEqual("0B", utils.make_size_human_readable(None))

    def test_get_new_file_size(self):
        size = 98304
        file_obj = six.StringIO('X' * size)
        try:
            self.assertEqual(size, utils.get_file_size(file_obj))
            # Check that get_file_size didn't change original file position.
            self.assertEqual(0, file_obj.tell())
        finally:
            file_obj.close()

    def test_get_consumed_file_size(self):
        size, consumed = 98304, 304
        file_obj = six.StringIO('X' * size)
        file_obj.seek(consumed)
        try:
            self.assertEqual(size, utils.get_file_size(file_obj))
            # Check that get_file_size didn't change original file position.
            self.assertEqual(consumed, file_obj.tell())
        finally:
            file_obj.close()

    def test_prettytable(self):
        class Struct(object):
            def __init__(self, **entries):
                self.__dict__.update(entries)

        # test that the prettytable output is wellformatted (left-aligned)
        columns = ['ID', 'Name']
        val = ['Name1', 'another', 'veeeery long']
        images = [Struct(**{'id': i ** 16, 'name': val[i]})
                  for i in range(len(val))]

        saved_stdout = sys.stdout
        try:
            sys.stdout = output_list = six.StringIO()
            utils.print_list(images, columns)

            sys.stdout = output_dict = six.StringIO()
            utils.print_dict({'K': 'k', 'Key': 'veeeeeeeeeeeeeeeeeeeeeeee'
                              'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'
                              'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'
                              'eeeeeeeeeeeery long value'},
                             max_column_width=60)

        finally:
            sys.stdout = saved_stdout

        self.assertEqual('''\
+-------+--------------+
| ID    | Name         |
+-------+--------------+
|       | Name1        |
| 1     | another      |
| 65536 | veeeery long |
+-------+--------------+
''',
                         output_list.getvalue())

        self.assertEqual('''\
+----------+--------------------------------------------------------------+
| Property | Value                                                        |
+----------+--------------------------------------------------------------+
| K        | k                                                            |
| Key      | veeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee |
|          | eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee |
|          | ery long value                                               |
+----------+--------------------------------------------------------------+
''',
                         output_dict.getvalue())

    def test_print_list_with_list_no_unicode(self):
        class Struct(object):
            def __init__(self, **entries):
                self.__dict__.update(entries)

        # test for removing 'u' from lists in print_list output
        columns = ['ID', 'Tags']
        images = [Struct(**{'id': 'b8e1c57e-907a-4239-aed8-0df8e54b8d2d',
                  'tags': [u'Name1', u'Tag_123', u'veeeery long']})]
        saved_stdout = sys.stdout
        try:
            sys.stdout = output_list = six.StringIO()
            utils.print_list(images, columns)

        finally:
            sys.stdout = saved_stdout

        self.assertEqual('''\
+--------------------------------------+--------------------------------------+
| ID                                   | Tags                                 |
+--------------------------------------+--------------------------------------+
| b8e1c57e-907a-4239-aed8-0df8e54b8d2d | ['Name1', 'Tag_123', 'veeeery long'] |
+--------------------------------------+--------------------------------------+
''',
                         output_list.getvalue())

    def test_print_image_virtual_size_available(self):
        image = {'id': '42', 'virtual_size': 1337}
        saved_stdout = sys.stdout
        try:
            sys.stdout = output_list = six.StringIO()
            utils.print_image(image)
        finally:
            sys.stdout = saved_stdout

        self.assertEqual('''\
+--------------+-------+
| Property     | Value |
+--------------+-------+
| id           | 42    |
| virtual_size | 1337  |
+--------------+-------+
''',
                         output_list.getvalue())

    def test_print_image_virtual_size_not_available(self):
        image = {'id': '42', 'virtual_size': None}
        saved_stdout = sys.stdout
        try:
            sys.stdout = output_list = six.StringIO()
            utils.print_image(image)
        finally:
            sys.stdout = saved_stdout

        self.assertEqual('''\
+--------------+---------------+
| Property     | Value         |
+--------------+---------------+
| id           | 42            |
| virtual_size | Not available |
+--------------+---------------+
''',
                         output_list.getvalue())

    def test_unicode_key_value_to_string(self):
        src = {u'key': u'\u70fd\u7231\u5a77'}
        expected = {'key': '\xe7\x83\xbd\xe7\x88\xb1\xe5\xa9\xb7'}
        if six.PY2:
            self.assertEqual(expected, utils.unicode_key_value_to_string(src))
        else:
            # u'xxxx' in PY3 is str, we will not get extra 'u' from cli
            # output in PY3
            self.assertEqual(src, utils.unicode_key_value_to_string(src))

    def test_schema_args_with_list_types(self):
        # NOTE(flaper87): Regression for bug
        # https://bugs.launchpad.net/python-glanceclient/+bug/1401032

        def schema_getter(_type='string', enum=False):
            prop = {
                'type': ['null', _type],
                'readOnly': True,
                'description': 'Test schema',
            }

            if enum:
                prop['enum'] = [None, 'opt-1', 'opt-2']

            def actual_getter():
                return {
                    'additionalProperties': False,
                    'required': ['name'],
                    'name': 'test_schema',
                    'properties': {
                        'test': prop,
                    }
                }

            return actual_getter

        def dummy_func():
            pass

        decorated = utils.schema_args(schema_getter())(dummy_func)
        arg, opts = decorated.__dict__['arguments'][0]
        self.assertIn('--test', arg)
        self.assertEqual(encodeutils.safe_decode, opts['type'])

        decorated = utils.schema_args(schema_getter('integer'))(dummy_func)
        arg, opts = decorated.__dict__['arguments'][0]
        self.assertIn('--test', arg)
        self.assertEqual(int, opts['type'])

        decorated = utils.schema_args(schema_getter(enum=True))(dummy_func)
        arg, opts = decorated.__dict__['arguments'][0]
        self.assertIn('--test', arg)
        self.assertEqual(encodeutils.safe_decode, opts['type'])
        self.assertIn('None, opt-1, opt-2', opts['help'])

    def test_iterable_closes(self):
        # Regression test for bug 1461678.
        def _iterate(i):
            for chunk in i:
                raise(IOError)

        data = six.moves.StringIO('somestring')
        data.close = mock.Mock()
        i = utils.IterableWithLength(data, 10)
        self.assertRaises(IOError, _iterate, i)
        data.close.assert_called_with()

    def test_safe_header(self):
        self.assertEqual(('somekey', 'somevalue'),
                         utils.safe_header('somekey', 'somevalue'))
        self.assertEqual(('somekey', None),
                         utils.safe_header('somekey', None))

        for sensitive_header in utils.SENSITIVE_HEADERS:
            (name, value) = utils.safe_header(
                sensitive_header,
                encodeutils.safe_encode('somestring'))
            self.assertEqual(sensitive_header, name)
            self.assertTrue(value.startswith("{SHA1}"))

            (name, value) = utils.safe_header(sensitive_header, None)
            self.assertEqual(sensitive_header, name)
            self.assertIsNone(value)

    def test_generator_proxy(self):
        def _test_decorator():
            i = 1
            resp = create_response_obj_with_req_id(REQUEST_ID)
            while True:
                yield i, resp
                i += 1

        gen_obj = _test_decorator()
        proxy = utils.GeneratorProxy(gen_obj)

        # Proxy object should succeed in behaving as the
        # wrapped object
        self.assertIsInstance(proxy, type(gen_obj))

        # Initially request_ids should be empty
        self.assertEqual([], proxy.request_ids)

        # Only after we have started iterating we should
        # see non-empty `request_ids` property
        proxy.next()
        self.assertEqual([REQUEST_ID], proxy.request_ids)

        # Even after multiple iterations `request_ids` property
        # should only contain one request id
        proxy.next()
        proxy.next()
        self.assertEqual(1, len(proxy.request_ids))

    def test_request_id_proxy(self):
        def test_data(val):
            resp = create_response_obj_with_req_id(REQUEST_ID)
            return val, resp

        # Object of any type except decorator can be passed to test_data
        proxy = utils.RequestIdProxy(test_data(11))
        # Verify that proxy object has a property `request_ids` and it is
        # a list of one request id
        self.assertEqual([REQUEST_ID], proxy.request_ids)
