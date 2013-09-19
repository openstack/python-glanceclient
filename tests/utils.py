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

import copy
import requests
import StringIO
import testtools

from glanceclient.common import http


class FakeAPI(object):
    def __init__(self, fixtures):
        self.fixtures = fixtures
        self.calls = []

    def _request(self, method, url, headers=None, body=None):
        call = (method, url, headers or {}, body)
        self.calls.append(call)
        return self.fixtures[url][method]

    def raw_request(self, *args, **kwargs):
        fixture = self._request(*args, **kwargs)
        resp = FakeResponse(fixture[0], StringIO.StringIO(fixture[1]))
        body_iter = http.ResponseBodyIterator(resp)
        return resp, body_iter

    def json_request(self, *args, **kwargs):
        fixture = self._request(*args, **kwargs)
        return FakeResponse(fixture[0]), fixture[1]


class FakeResponse(object):
    def __init__(self, headers, body=None,
                 version=1.0, status=200, reason="Ok"):
        """
        :param headers: dict representing HTTP response headers
        :param body: file-like object
        :param version: HTTP Version
        :param status: Response status code
        :param reason: Status code related message.
        """
        self.body = body
        self.status = status
        self.reason = reason
        self.version = version
        self.headers = headers

    def getheaders(self):
        return copy.deepcopy(self.headers).items()

    def getheader(self, key, default):
        return self.headers.get(key, default)

    def read(self, amt):
        return self.body.read(amt)


class TestCase(testtools.TestCase):
    TEST_REQUEST_BASE = {
        'config': {'danger_mode': False},
        'verify': True}


class TestResponse(requests.Response):
    """
    Class used to wrap requests.Response and provide some
    convenience to initialize with a dict
    """
    def __init__(self, data):
        self._text = None
        super(TestResponse, self)
        if isinstance(data, dict):
            self.status_code = data.get('status_code', None)
            self.headers = data.get('headers', None)
            # Fake the text attribute to streamline Response creation
            self._text = data.get('text', None)
        else:
            self.status_code = data

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @property
    def text(self):
        return self._text


class FakeTTYStdout(StringIO.StringIO):
    """A Fake stdout that try to emulate a TTY device as much as possible."""

    def isatty(self):
        return True

    def write(self, data):
        # When a CR (carriage return) is found reset file.
        if data.startswith('\r'):
            self.seek(0)
            data = data[1:]
        return StringIO.StringIO.write(self, data)
