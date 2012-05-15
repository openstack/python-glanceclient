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
        if 'raw_body' in kwargs:
            logger.debug("REQ BODY (RAW): %s\n" % (kwargs['raw_body']))
        if 'body' in kwargs:
            logger.debug("REQ BODY: %s\n" % (kwargs['body']))
        logger.debug("RESP: %s\nRESP BODY: %s\n", resp, body)

    def _http_request(self, url, method, **kwargs):
        """ Send an http request with the specified characteristics.

        Wrapper around httplib2.Http.request to handle tasks such as
        setting headers, JSON encoding/decoding, and error handling.
        """
        url = self.endpoint + url

        # Copy the kwargs so we can reuse the original in case of redirects
        kwargs['headers'] = copy.deepcopy(kwargs.get('headers', {}))
        kwargs['headers'].setdefault('User-Agent', USER_AGENT)
        if self.auth_token:
            kwargs['headers'].setdefault('X-Auth-Token', self.auth_token)

        resp, body = super(HTTPClient, self).request(url, method, **kwargs)
        self.http_log((url, method,), kwargs, resp, body)

        if 400 <= resp.status < 600:
            logger.exception("Request returned failure status.")
            raise exceptions.from_response(resp, body)
        elif resp.status in (301, 302, 305):
            # Redirected. Reissue the request to the new location.
            return self._http_request(resp['location'], method, **kwargs)

        return resp, body

    def json_request(self, method, url, **kwargs):
        kwargs.setdefault('headers', {})
        kwargs['headers'].setdefault('Content-Type', 'application/json')

        if 'body' in kwargs:
            kwargs['body'] = json.dumps(kwargs['body'])

        resp, body = self._http_request(url, method, **kwargs)

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
