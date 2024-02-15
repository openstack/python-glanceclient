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

from glanceclient.tests.functional import base
import time


IMAGE = {"protected": False,
         "disk_format": "qcow2",
         "name": "glance_functional_test_image.img",
         "visibility": "private",
         "container_format": "bare"}


class HttpHeadersTest(base.ClientTestBase):
    def test_encode_headers_python(self):
        """Test proper handling of Content-Type headers.

        encode_headers() must be called as late as possible before a
        request is sent. If this principle is violated, and if any
        changes are made to the headers between encode_headers() and the
        actual request (for instance a call to
        _set_common_request_kwargs()), and if you're trying to set a
        Content-Type that is not equal to application/octet-stream (the
        default), it is entirely possible that you'll end up with two
        Content-Type headers defined (yours plus
        application/octet-stream). The request will go out the door with
        only one of them chosen seemingly at random.

        This test uses a call to update() because it sets a header such
        as the following (this example may be subject to change):
        Content-Type: application/openstack-images-v2.1-json-patch

        This situation only occurs in python3. This test will never fail
        in python2.

        There is no test against the CLI because it swallows the error.
        """
        # the failure is intermittent - try up to 6 times
        for attempt in range(0, 6):
            glanceclient = self.glance_pyclient()
            image = glanceclient.find(IMAGE["name"])
            if image:
                glanceclient.glance.images.delete(image.id)
            image = glanceclient.glance.images.create(name=IMAGE["name"])
            self.assertTrue(image.status == "queued")
            try:
                image = glanceclient.glance.images.update(image.id,
                                                          disk_format="qcow2")
            except Exception as e:
                self.assertNotIn("415 Unsupported Media Type", e.details)
            time.sleep(5)
