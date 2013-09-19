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

import urllib

import warlock

from glanceclient.openstack.common import strutils

DEFAULT_PAGE_SIZE = 20


class Controller(object):
    def __init__(self, http_client, model):
        self.http_client = http_client
        self.model = model

    def list(self, **kwargs):
        """Retrieve a listing of Image objects

        :param page_size: Number of images to request in each paginated request
        :returns generator over list of Images
        """
        def paginate(url):
            resp, body = self.http_client.json_request('GET', url)
            for image in body['images']:
                yield image
            try:
                next_url = body['next']
            except KeyError:
                return
            else:
                for image in paginate(next_url):
                    yield image

        filters = kwargs.get('filters', {})

        if not kwargs.get('page_size'):
            filters['limit'] = DEFAULT_PAGE_SIZE
        else:
            filters['limit'] = kwargs['page_size']

        tags = filters.pop('tag', [])
        tags_url_params = []

        for tag in tags:
            if isinstance(tag, basestring):
                tags_url_params.append({'tag': strutils.safe_encode(tag)})

        for param, value in filters.iteritems():
            if isinstance(value, basestring):
                filters[param] = strutils.safe_encode(value)

        url = '/v2/images?%s' % urllib.urlencode(filters)

        for param in tags_url_params:
            url = '%s&%s' % (url, urllib.urlencode(param))

        for image in paginate(url):
            #NOTE(bcwaldon): remove 'self' for now until we have an elegant
            # way to pass it into the model constructor without conflict
            image.pop('self', None)
            yield self.model(**image)

    def get(self, image_id):
        url = '/v2/images/%s' % image_id
        resp, body = self.http_client.json_request('GET', url)
        #NOTE(bcwaldon): remove 'self' for now until we have an elegant
        # way to pass it into the model constructor without conflict
        body.pop('self', None)
        return self.model(**body)

    def data(self, image_id, do_checksum=True):
        """
        Retrieve data of an image.

        :param image_id:    ID of the image to download.
        :param do_checksum: Enable/disable checksum validation.
        """
        url = '/v2/images/%s/file' % image_id
        resp, body = self.http_client.raw_request('GET', url)
        checksum = resp.getheader('content-md5', None)
        if do_checksum and checksum is not None:
            body.set_checksum(checksum)
        return body

    def upload(self, image_id, image_data):
        """
        Upload the data for an image.

        :param image_id: ID of the image to upload data for.
        :param image_data: File-like object supplying the data to upload.
        """
        url = '/v2/images/%s/file' % image_id
        hdrs = {'Content-Type': 'application/octet-stream'}
        self.http_client.raw_request('PUT', url,
                                     headers=hdrs,
                                     body=image_data)

    def delete(self, image_id):
        """Delete an image."""
        self.http_client.json_request('DELETE', 'v2/images/%s' % image_id)

    def create(self, **kwargs):
        """Create an image."""
        url = '/v2/images'

        image = self.model()
        for (key, value) in kwargs.items():
            try:
                setattr(image, key, value)
            except warlock.InvalidOperation as e:
                raise TypeError(unicode(e))

        resp, body = self.http_client.json_request('POST', url, body=image)
        #NOTE(esheffield): remove 'self' for now until we have an elegant
        # way to pass it into the model constructor without conflict
        body.pop('self', None)
        return self.model(**body)

    def update(self, image_id, remove_props=None, **kwargs):
        """
        Update attributes of an image.

        :param image_id: ID of the image to modify.
        :param remove_props: List of property names to remove
        :param **kwargs: Image attribute names and their new values.
        """
        image = self.get(image_id)
        for (key, value) in kwargs.items():
            try:
                setattr(image, key, value)
            except warlock.InvalidOperation as e:
                raise TypeError(unicode(e))

        if remove_props is not None:
            cur_props = image.keys()
            new_props = kwargs.keys()
            #NOTE(esheffield): Only remove props that currently exist on the
            # image and are NOT in the properties being updated / added
            props_to_remove = set(cur_props).intersection(
                set(remove_props).difference(new_props))

            for key in props_to_remove:
                delattr(image, key)

        url = '/v2/images/%s' % image_id
        hdrs = {'Content-Type': 'application/openstack-images-v2.1-json-patch'}
        self.http_client.raw_request('PATCH', url,
                                     headers=hdrs,
                                     body=image.patch)

        #NOTE(bcwaldon): calling image.patch doesn't clear the changes, so
        # we need to fetch the image again to get a clean history. This is
        # an obvious optimization for warlock
        return self.get(image_id)
