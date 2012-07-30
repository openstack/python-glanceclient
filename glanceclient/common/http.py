"""
OpenStack Client interface. Handles the REST calls and responses.
"""

import copy
import httplib
import logging
import StringIO
import urlparse


try:
    import json
except ImportError:
    import simplejson as json

# Python 2.5 compat fix
if not hasattr(urlparse, 'parse_qsl'):
    import cgi
    urlparse.parse_qsl = cgi.parse_qsl


from glanceclient import exc


LOG = logging.getLogger(__name__)
USER_AGENT = 'python-glanceclient'
CHUNKSIZE = 1024 * 64  # 64kB


class HTTPClient(object):

    def __init__(self, endpoint, token=None, timeout=600, insecure=False):
        parts = urlparse.urlparse(endpoint)
        self.connection_class = self.get_connection_class(parts.scheme)
        self.endpoint = (parts.hostname, parts.port)
        self.scheme = parts.scheme
        self.auth_token = token

    @staticmethod
    def get_connection_class(scheme):
        try:
            return getattr(httplib, '%sConnection' % scheme.upper())
        except AttributeError:
            msg = 'Unsupported scheme: %s' % scheme
            raise exc.InvalidEndpoint(msg)

    def get_connection(self):
        return self.connection_class(*self.endpoint)

    def log_curl_request(self, method, url, kwargs):
        curl = ['curl -i -X %s' % method]

        for (key, value) in kwargs['headers'].items():
            header = '-H \'%s: %s\'' % (key, value)
            curl.append(header)

        if 'body' in kwargs:
            curl.append('-d \'%s\'' % kwargs['body'])

        endpoint_parts = (self.scheme, self.endpoint[0], self.endpoint[1], url)
        curl.append('%s://%s:%s%s' % endpoint_parts)
        LOG.debug(' '.join(curl))

    @staticmethod
    def log_http_response(resp, body=None):
        status = (resp.version / 10.0, resp.status, resp.reason)
        dump = ['\nHTTP/%.1f %s %s' % status]
        dump.extend(['%s: %s' % (k, v) for k, v in resp.getheaders()])
        dump.append('')
        if body:
            dump.extend([body, ''])
        LOG.debug('\n'.join(dump))

    def _http_request(self, url, method, **kwargs):
        """ Send an http request with the specified characteristics.

        Wrapper around httplib.HTTP(S)Connection.request to handle tasks such
        as setting headers and error handling.
        """
        # Copy the kwargs so we can reuse the original in case of redirects
        kwargs['headers'] = copy.deepcopy(kwargs.get('headers', {}))
        kwargs['headers'].setdefault('User-Agent', USER_AGENT)
        if self.auth_token:
            kwargs['headers'].setdefault('X-Auth-Token', self.auth_token)

        self.log_curl_request(method, url, kwargs)

        conn = self.get_connection()
        conn.request(method, url, **kwargs)
        resp = conn.getresponse()

        body_iter = ResponseBodyIterator(resp)

        # Read body into string if it isn't obviously image data
        if resp.getheader('content-type', None) != 'application/octet-stream':
            body_str = ''.join([chunk for chunk in body_iter])
            self.log_http_response(resp, body_str)
            body_iter = StringIO.StringIO(body_str)
        else:
            self.log_http_response(resp)

        if 400 <= resp.status < 600:
            LOG.exception("Request returned failure status.")
            raise exc.from_response(resp)
        elif resp.status in (301, 302, 305):
            # Redirected. Reissue the request to the new location.
            return self._http_request(resp['location'], method, **kwargs)

        return resp, body_iter

    def json_request(self, method, url, **kwargs):
        kwargs.setdefault('headers', {})
        kwargs['headers'].setdefault('Content-Type', 'application/json')

        if 'body' in kwargs:
            kwargs['body'] = json.dumps(kwargs['body'])

        resp, body_iter = self._http_request(url, method, **kwargs)

        if 'application/json' in resp.getheader('content-type', None):
            body = ''.join([chunk for chunk in body_iter])
            try:
                body = json.loads(body)
            except ValueError:
                LOG.error('Could not decode response body as JSON')
        else:
            body = None

        return resp, body

    def raw_request(self, method, url, **kwargs):
        kwargs.setdefault('headers', {})
        kwargs['headers'].setdefault('Content-Type',
                                     'application/octet-stream')
        return self._http_request(url, method, **kwargs)


class ResponseBodyIterator(object):
    """A class that acts as an iterator over an HTTP response."""

    def __init__(self, resp):
        self.resp = resp

    def __iter__(self):
        while True:
            yield self.next()

    def next(self):
        chunk = self.resp.read(CHUNKSIZE)
        if chunk:
            return chunk
        else:
            raise StopIteration()
