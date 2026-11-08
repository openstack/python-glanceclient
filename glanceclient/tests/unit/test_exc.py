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
import testtools
from unittest import mock

from glanceclient import exc

HTML_MSG = """<html>
 <head>
   <title>404 Entity Not Found</title>
 </head>
 <body>
  <h1>404 Entity Not Found</h1>
  Entity could not be found
  <br /><br />
 </body>
</html>"""


class TestHTTPExceptions(testtools.TestCase):
    def test_from_response(self):
        """exc.from_response should return instance of an HTTP exception."""
        mock_resp = mock.Mock()
        mock_resp.status_code = 400
        out = exc.from_response(mock_resp)
        self.assertIsInstance(out, exc.HTTPBadRequest)

    def test_handles_json(self):
        """Extract the top-level message from Glance's JSON error response."""
        for status, title, message, exception in (
                (404, 'Not Found', 'Image not found', exc.HTTPNotFound),
                (413, 'Request Entity Too Large', 'Image quota exceeded',
                 exc.HTTPOverLimit)):
            with self.subTest(status=status):
                mock_resp = mock.Mock()
                mock_resp.status_code = status
                mock_resp.json.return_value = {
                    'code': '%s %s' % (status, title),
                    'title': title,
                    'message': message,
                }
                mock_resp.headers = {'content-type': 'application/json'}
                err = exc.from_response(mock_resp, b'Non-empty body')
                self.assertIsInstance(err, exception)
                self.assertEqual(message, err.details)

    def test_handles_json_without_message(self):
        for data in (
                {'code': '404 Not Found', 'title': 'Not Found'},
                {'message': None},
                {'message': 404},
                {'message': ['Not found']},
                {'message': {'detail': 'Not found'}},
                [], None, 'Not found'):
            with self.subTest(data=data):
                mock_resp = mock.Mock()
                mock_resp.status_code = 404
                mock_resp.json.return_value = data
                mock_resp.headers = {'content-type': 'application/json'}
                err = exc.from_response(mock_resp, b'Non-empty body')
                self.assertIsInstance(err, exc.HTTPNotFound)
                self.assertEqual('HTTPNotFound', err.details)

    def test_handles_html(self):
        """exc.from_response should not print HTML."""
        mock_resp = mock.Mock()
        mock_resp.status_code = 404
        mock_resp.text = HTML_MSG
        mock_resp.headers = {
            "content-type": "text/html"
        }
        err = exc.from_response(mock_resp, HTML_MSG)
        self.assertIsInstance(err, exc.HTTPNotFound)
        self.assertEqual("404 Entity Not Found: Entity could not be found",
                         err.details)

    def test_format_no_content_type(self):
        mock_resp = mock.Mock()
        mock_resp.status_code = 400
        mock_resp.headers = {'content-type': 'application/octet-stream'}
        body = b'Error \n\n'
        err = exc.from_response(mock_resp, body)
        self.assertEqual('Error \n', err.details)
