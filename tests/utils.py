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
import json
import six
import testtools


class FakeAPI(object):
    def __init__(self, fixtures):
        self.fixtures = fixtures
        self.calls = []

    def _request(self, method, url, headers=None, data=None,
                 content_length=None):
        call = (method, url, headers or {}, data)
        if content_length is not None:
            call = tuple(list(call) + [content_length])
        self.calls.append(call)
        fixture = self.fixtures[url][method]

        data = fixture[1]
        if isinstance(fixture[1], six.string_types):
            try:
                data = json.loads(fixture[1])
            except ValueError:
                data = six.StringIO(fixture[1])

        return FakeResponse(fixture[0], fixture[1]), data

    def get(self, *args, **kwargs):
        return self._request('GET', *args, **kwargs)

    def post(self, *args, **kwargs):
        return self._request('POST', *args, **kwargs)

    def put(self, *args, **kwargs):
        return self._request('PUT', *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self._request('PATCH', *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._request('DELETE', *args, **kwargs)

    def head(self, *args, **kwargs):
        return self._request('HEAD', *args, **kwargs)


class RawRequest(object):
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


class FakeResponse(object):
    def __init__(self, headers=None, body=None,
                 version=1.0, status_code=200, reason="Ok"):
        """
        :param headers: dict representing HTTP response headers
        :param body: file-like object
        :param version: HTTP Version
        :param status: Response status code
        :param reason: Status code related message.
        """
        self.body = body
        self.reason = reason
        self.version = version
        self.headers = headers
        self.status_code = status_code
        self.raw = RawRequest(headers, body=body, reason=reason,
                              version=version, status=status_code)

    @property
    def ok(self):
        return (self.status_code < 400 or
                self.status_code >= 600)

    def read(self, amt):
        return self.body.read(amt)

    @property
    def content(self):
        if hasattr(self.body, "read"):
            return self.body.read()
        return self.body

    def json(self, **kwargs):
        return self.body and json.loads(self.content) or ""

    def iter_content(self, chunk_size=1, decode_unicode=False):
        while True:
            chunk = self.raw.read(chunk_size)
            if not chunk:
                break
            yield chunk


class TestCase(testtools.TestCase):
    TEST_REQUEST_BASE = {
        'config': {'danger_mode': False},
        'verify': True}


class FakeTTYStdout(six.StringIO):
    """A Fake stdout that try to emulate a TTY device as much as possible."""

    def isatty(self):
        return True

    def write(self, data):
        # When a CR (carriage return) is found reset file.
        if data.startswith('\r'):
            self.seek(0)
            data = data[1:]
        return six.StringIO.write(self, data)


class FakeNoTTYStdout(FakeTTYStdout):
    """A Fake stdout that is not a TTY device."""

    def isatty(self):
        return False
