"""
OpenStack Client interface. Handles the REST calls and responses.
"""

import copy
import httplib
import logging
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


logger = logging.getLogger(__name__)
USER_AGENT = 'python-glanceclient'
CHUNKSIZE = 1024 * 64  # 64kB


class HTTPClient(object):

    def __init__(self, endpoint, token=None, timeout=600, insecure=False):
        parts = urlparse.urlparse(endpoint)
        self.connection_class = self.get_connection_class(parts.scheme)
        self.endpoint = (parts.hostname, parts.port)
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

    def http_log(self, args, kwargs, resp):
        string_parts = ['curl -i']
        for element in args:
            if element in ('GET', 'POST'):
                string_parts.append(' -X %s' % element)
            else:
                string_parts.append(' %s' % element)

        for element in kwargs['headers']:
            header = ' -H "%s: %s"' % (element, kwargs['headers'][element])
            string_parts.append(header)

        logger.debug("REQ: %s\n" % "".join(string_parts))
        if 'raw_body' in kwargs:
            logger.debug("REQ BODY (RAW): %s\n" % (kwargs['raw_body']))
        if 'body' in kwargs:
            logger.debug("REQ BODY: %s\n" % (kwargs['body']))
        logger.debug("RESP: %s", resp)

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

        conn = self.get_connection()
        conn.request(method, url, **kwargs)
        resp = conn.getresponse()

        self.http_log((url, method,), kwargs, resp)

        if 400 <= resp.status < 600:
            logger.exception("Request returned failure status.")
            raise exc.from_response(resp)
        elif resp.status in (301, 302, 305):
            # Redirected. Reissue the request to the new location.
            return self._http_request(resp['location'], method, **kwargs)

        body_iter = ResponseBodyIterator(resp)
        return resp, body_iter

    def json_request(self, method, url, **kwargs):
        kwargs.setdefault('headers', {})
        kwargs['headers'].setdefault('Content-Type', 'application/json')

        if 'body' in kwargs:
            kwargs['body'] = json.dumps(kwargs['body'])

        resp, body_iter = self._http_request(url, method, **kwargs)
        body = ''.join([chunk for chunk in body_iter])

        if body:
            try:
                body = json.loads(body)
            except ValueError:
                logger.debug("Could not decode JSON from body: %s" % body)
        else:
            logger.debug("No body was returned.")
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
