# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 OpenStack LLC.
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

import logging
import urlparse

from glanceclient import client
from glanceclient import exceptions

_logger = logging.getLogger(__name__)


class Client(client.HTTPClient):
    """Client for the OpenStack Images pre-version calls API.

    :param string endpoint: A user-supplied endpoint URL for the glance
                            service.
    :param integer timeout: Allows customization of the timeout for client
                            http requests. (optional)

    Example::

        >>> from glanceclient.generic import client
        >>> root = client.Client(auth_url=KEYSTONE_URL)
        >>> versions = root.discover()
        ...
        >>> from glanceclient.v1_1 import client as v11client
        >>> glance = v11client.Client(auth_url=versions['v1.1']['url'])
        ...
        >>> image = glance.images.get(IMAGE_ID)
        >>> image.delete()

    """

    def __init__(self, endpoint=None, **kwargs):
        """ Initialize a new client for the Glance v2.0 API. """
        super(Client, self).__init__(endpoint=endpoint, **kwargs)
        self.endpoint = endpoint

    def discover(self, url=None):
        """ Discover Glance servers and return API versions supported.

        :param url: optional url to test (without version)

        Returns::

            {
                'message': 'Glance found at http://127.0.0.1:5000/',
                'v2.0': {
                    'status': 'beta',
                    'url': 'http://127.0.0.1:5000/v2.0/',
                    'id': 'v2.0'
                },
            }

        """
        if url:
            return self._check_glance_versions(url)
        else:
            return self._local_glance_exists()

    def _local_glance_exists(self):
        """ Checks if Glance is available on default local port 9292 """
        return self._check_glance_versions("http://localhost:9292")

    def _check_glance_versions(self, url):
        """ Calls Glance URL and detects the available API versions """
        try:
            httpclient = client.HTTPClient()
            resp, body = httpclient.request(url, "GET",
                                      headers={'Accept': 'application/json'})
            if resp.status in (300):  # Glance returns a 300 Multiple Choices
                try:
                    results = {}
                    if 'version' in body:
                        results['message'] = "Glance found at %s" % url
                        version = body['version']
                        # Stable/diablo incorrect format
                        id, status, version_url = self._get_version_info(
                                                                version, url)
                        results[str(id)] = {"id": id,
                                            "status": status,
                                            "url": version_url}
                        return results
                    elif 'versions' in body:
                        # Correct format
                        results['message'] = "Glance found at %s" % url
                        for version in body['versions']['values']:
                            id, status, version_url = self._get_version_info(
                                                                version, url)
                            results[str(id)] = {"id": id,
                                                "status": status,
                                                "url": version_url}
                        return results
                    else:
                        results['message'] = "Unrecognized response from %s" \
                                        % url
                    return results
                except KeyError:
                    raise exceptions.AuthorizationFailure()
            elif resp.status == 305:
                return self._check_glance_versions(resp['location'])
            else:
                raise exceptions.from_response(resp, body)
        except Exception as e:
            _logger.exception(e)

    def discover_extensions(self, url=None):
        """ Discover Glance extensions supported.

        :param url: optional url to test (should have a version in it)

        Returns::

            {
                'message': 'Glance extensions at http://127.0.0.1:35357/v2',
                'OS-KSEC2': 'OpenStack EC2 Credentials Extension',
            }

        """
        if url:
            return self._check_glance_extensions(url)

    def _check_glance_extensions(self, url):
        """ Calls Glance URL and detects the available extensions """
        try:
            httpclient = client.HTTPClient()
            if not url.endswith("/"):
                url += '/'
            resp, body = httpclient.request("%sextensions" % url, "GET",
                                      headers={'Accept': 'application/json'})
            if resp.status in (200, 204):  # in some cases we get No Content
                try:
                    results = {}
                    if 'extensions' in body:
                        if 'values' in body['extensions']:
                            # Parse correct format (per contract)
                            for extension in body['extensions']['values']:
                                alias, name = self._get_extension_info(
                                        extension['extension'])
                                results[alias] = name
                            return results
                        else:
                            # Support incorrect, but prevalent format
                            for extension in body['extensions']:
                                alias, name = self._get_extension_info(
                                        extension)
                                results[alias] = name
                            return results
                    else:
                        results['message'] = "Unrecognized extensions" \
                                " response from %s" % url
                    return results
                except KeyError:
                    raise exceptions.AuthorizationFailure()
            elif resp.status == 305:
                return self._check_glance_extensions(resp['location'])
            else:
                raise exceptions.from_response(resp, body)
        except Exception as e:
            _logger.exception(e)

    @staticmethod
    def _get_version_info(version, root_url):
        """ Parses version information

        :param version: a dict of a Glance version response
        :param root_url: string url used to construct
            the version if no URL is provided.
        :returns: tuple - (verionId, versionStatus, versionUrl)
        """
        id = version['id']
        status = version['status']
        ref = urlparse.urljoin(root_url, id)
        if 'links' in version:
            for link in version['links']:
                if link['rel'] == 'self':
                    ref = link['href']
                    break
        return (id, status, ref)

    @staticmethod
    def _get_extension_info(extension):
        """ Parses extension information

        :param extension: a dict of a Glance extension response
        :returns: tuple - (alias, name)
        """
        alias = extension['alias']
        name = extension['name']
        return (alias, name)
