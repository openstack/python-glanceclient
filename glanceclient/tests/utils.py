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
from email.message import EmailMessage
import io
import json
import testtools
from urllib import parse

from glanceclient.v2 import schemas


class FakeAPI(object):
    def __init__(self, fixtures):
        self.fixtures = fixtures
        self.calls = []

    def _request(self, method, url, headers=None, data=None,
                 content_length=None):
        call = build_call_record(method, sort_url_by_query_keys(url),
                                 headers or {}, data)
        if content_length is not None:
            call = tuple(list(call) + [content_length])
        self.calls.append(call)

        fixture = self.fixtures[sort_url_by_query_keys(url)][method]

        data = fixture[1]
        if isinstance(fixture[1], str):
            try:
                data = json.loads(fixture[1])
            except ValueError:
                data = io.StringIO(fixture[1])

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


class FakeSchemaAPI(FakeAPI):
    def get(self, *args, **kwargs):
        _, raw_schema = self._request('GET', *args, **kwargs)
        return schemas.Schema(raw_schema)


class RawRequest(object):
    def __init__(self, headers, body=None,
                 version=1.0, status=200, reason="Ok"):
        """A crafted request object used for testing.

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
        """A crafted response object used for testing.

        :param headers: dict representing HTTP response headers
        :param body: file-like object
        :param version: HTTP Version
        :param status: Response status code
        :param reason: Status code related message.
        """
        self.body = body
        self.reason = reason
        self.version = version
        # NOTE(tkajinam): Make the FakeResponse class compatible with
        # http.client.HTTPResponse
        # https://docs.python.org/3/library/http.client.html
        self.headers = EmailMessage()
        for header_key in headers:
            self.headers[header_key] = headers[header_key]
        self.headers['x-openstack-request-id'] = 'req-1234'
        self.status_code = status_code
        self.raw = RawRequest(headers, body=body, reason=reason,
                              version=version, status=status_code)

    @property
    def status(self):
        return self.status_code

    @property
    def ok(self):
        return (self.status_code < 400 or
                self.status_code >= 600)

    def read(self, amt):
        return self.body.read(amt)

    def close(self):
        pass

    @property
    def content(self):
        if hasattr(self.body, "read"):
            return self.body.read()
        return self.body

    @property
    def text(self):
        if isinstance(self.content, bytes):
            return self.content.decode('utf-8')

        return self.content

    def json(self, **kwargs):
        return self.body and json.loads(self.text) or ""

    def iter_content(self, chunk_size=1, decode_unicode=False):
        while True:
            chunk = self.raw.read(chunk_size)
            if not chunk:
                break
            yield chunk

    def release_conn(self, **kwargs):
        pass


class TestCase(testtools.TestCase):
    TEST_REQUEST_BASE = {
        'config': {'danger_mode': False},
        'verify': True}


class FakeTTYStdout(io.StringIO):
    """A Fake stdout that try to emulate a TTY device as much as possible."""

    def isatty(self):
        return True

    def write(self, data):
        # When a CR (carriage return) is found reset file.
        if data.startswith('\r'):
            self.seek(0)
            data = data[1:]
        return io.StringIO.write(self, data)


class FakeNoTTYStdout(FakeTTYStdout):
    """A Fake stdout that is not a TTY device."""

    def isatty(self):
        return False


def sort_url_by_query_keys(url):
    """A helper function which sorts the keys of the query string of a url.

       For example, an input of '/v2/tasks?sort_key=id&sort_dir=asc&limit=10'
       returns '/v2/tasks?limit=10&sort_dir=asc&sort_key=id'. This is to
       prevent non-deterministic ordering of the query string causing
       problems with unit tests.
    :param url: url which will be ordered by query keys
    :returns url: url with ordered query keys
    """
    parsed = parse.urlparse(url)
    queries = parse.parse_qsl(parsed.query, True)
    sorted_query = sorted(queries, key=lambda x: x[0])

    encoded_sorted_query = parse.urlencode(sorted_query, True)

    url_parts = (parsed.scheme, parsed.netloc, parsed.path,
                 parsed.params, encoded_sorted_query,
                 parsed.fragment)

    return parse.urlunparse(url_parts)


def build_call_record(method, url, headers, data):
    """Key the request body be ordered if it's a dict type."""
    if isinstance(data, dict):
        data = sorted(data.items())
    if isinstance(data, str):
        # NOTE(flwang): For image update, the data will be a 'list' which
        # contains operation dict, such as: [{"op": "remove", "path": "/a"}]
        try:
            data = json.loads(data)
        except ValueError:
            return (method, url, headers or {}, data)
        data = [sorted(d.items()) for d in data]
    return (method, url, headers or {}, data)
