# Copyright 2012 OpenStack LLC.
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

from glanceclient.common import utils

DEFAULT_PAGE_SIZE = 20


class Controller(object):
    def __init__(self, http_client, model):
        self.http_client = http_client
        self.model = model

    def list(self, page_size=DEFAULT_PAGE_SIZE):
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

        url = '/v2/images?limit=%s' % page_size

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
            return utils.integrity_iter(body, checksum)
        else:
            return body
