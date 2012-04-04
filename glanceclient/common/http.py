"""
OpenStack Client interface. Handles the REST calls and responses.
"""

import copy
import logging
import os
import urlparse

import httplib2

try:
    import json
except ImportError:
    import simplejson as json

# Python 2.5 compat fix
if not hasattr(urlparse, 'parse_qsl'):
    import cgi
    urlparse.parse_qsl = cgi.parse_qsl


from glanceclient.common import exceptions


logger = logging.getLogger(__name__)
USER_AGENT = 'python-glanceclient'


class HTTPClient(httplib2.Http):

    def __init__(self, endpoint, token=None, timeout=600):
        super(HTTPClient, self).__init__(timeout=timeout)
        self.endpoint = endpoint
        self.auth_token = token

        # httplib2 overrides
        self.force_exception_to_status_code = True

    def http_log(self, args, kwargs, resp, body):
        if os.environ.get('GLANCECLIENT_DEBUG', False):
            ch = logging.StreamHandler()
            logger.setLevel(logging.DEBUG)
            logger.addHandler(ch)
        elif not logger.isEnabledFor(logging.DEBUG):
            return

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
        if 'body' in kwargs:
            logger.debug("REQ BODY: %s\n" % (kwargs['body']))
        logger.debug("RESP: %s\nRESP BODY: %s\n", resp, body)

    def _http_request(self, url, method, **kwargs):
        """ Send an http request with the specified characteristics.

        Wrapper around httplib2.Http.request to handle tasks such as
        setting headers, JSON encoding/decoding, and error handling.
        """
        # Copy the kwargs so we can reuse the original in case of redirects
        _kwargs = copy.copy(kwargs)
        _kwargs.setdefault('headers', kwargs.get('headers', {}))
        _kwargs['headers']['User-Agent'] = USER_AGENT
        if 'body' in kwargs and kwargs['body'] is not None:
            _kwargs['headers']['Content-Type'] = 'application/octet-stream'
            _kwargs['body'] = kwargs['body']

        resp, body = super(HTTPClient, self).request(url, method, **_kwargs)
        self.http_log((url, method,), _kwargs, resp, body)

        if body:
            try:
                body = json.loads(body)
            except ValueError:
                logger.debug("Could not decode JSON from body: %s" % body)
        else:
            logger.debug("No body was returned.")
            body = None

        if 400 <= resp.status < 600:
            logger.exception("Request returned failure status.")
            raise exceptions.from_response(resp, body)
        elif resp.status in (301, 302, 305):
            # Redirected. Reissue the request to the new location.
            return self._http_request(resp['location'], method, **kwargs)

        return resp, body

    def request(self, url, method, **kwargs):
        kwargs.setdefault('headers', {})
        if self.auth_token:
            kwargs['headers']['X-Auth-Token'] = self.auth_token

        req_url = self.endpoint + url
        resp, body = self._http_request(req_url, method, **kwargs)
        return resp, body

    def head(self, url, **kwargs):
        return self.request(url, 'HEAD', **kwargs)

    def get(self, url, **kwargs):
        return self.request(url, 'GET', **kwargs)

    def post(self, url, **kwargs):
        return self.request(url, 'POST', **kwargs)

    def put(self, url, **kwargs):
        return self.request(url, 'PUT', **kwargs)

    def delete(self, url, **kwargs):
        return self.request(url, 'DELETE', **kwargs)
