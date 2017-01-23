# Copyright 2013 OpenStack Foundation
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

import testtools

from glanceclient.tests.unit.v2 import base
from glanceclient.tests import utils
from glanceclient.v2 import image_tags


IMAGE = '3a4560a1-e585-443e-9b39-553b46ec92d1'
TAG = 'tag01'


data_fixtures = {
    '/v2/images/{image}/tags/{tag_value}'.format(image=IMAGE, tag_value=TAG): {
        'DELETE': (
            {},
            None,
        ),
        'PUT': (
            {},
            {
                'image_id': IMAGE,
                'tag_value': TAG
            }
        ),
    }
}

schema_fixtures = {
    'tag': {
        'GET': (
            {},
            {'name': 'image', 'properties': {'image_id': {}, 'tags': {}}}
        )
    }
}


class TestController(testtools.TestCase):
    def setUp(self):
        super(TestController, self).setUp()
        self.api = utils.FakeAPI(data_fixtures)
        self.schema_api = utils.FakeSchemaAPI(schema_fixtures)
        self.controller = base.BaseController(self.api, self.schema_api,
                                              image_tags.Controller)

    def test_update_image_tag(self):
        image_id = IMAGE
        tag_value = TAG
        self.controller.update(image_id, tag_value)
        expect = [
            ('PUT',
             '/v2/images/{image}/tags/{tag_value}'.format(image=IMAGE,
                                                          tag_value=TAG),
             {},
             None)]
        self.assertEqual(expect, self.api.calls)

    def test_delete_image_tag(self):
        image_id = IMAGE
        tag_value = TAG
        self.controller.delete(image_id, tag_value)
        expect = [
            ('DELETE',
             '/v2/images/{image}/tags/{tag_value}'.format(image=IMAGE,
                                                          tag_value=TAG),
             {},
             None)]
        self.assertEqual(expect, self.api.calls)
