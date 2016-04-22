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
from glanceclient.v2 import image_members


IMAGE = '3a4560a1-e585-443e-9b39-553b46ec92d1'
MEMBER = '11223344-5566-7788-9911-223344556677'


data_fixtures = {
    '/v2/images/{image}/members'.format(image=IMAGE): {
        'GET': (
            {},
            {'members': [
                {
                    'image_id': IMAGE,
                    'member_id': MEMBER,
                },
            ]},
        ),
        'POST': (
            {},
            {
                'image_id': IMAGE,
                'member_id': MEMBER,
                'status': 'pending'
            }
        )
    },
    '/v2/images/{image}/members/{mem}'.format(image=IMAGE, mem=MEMBER): {
        'DELETE': (
            {},
            None,
        ),
        'PUT': (
            {},
            {
                'image_id': IMAGE,
                'member_id': MEMBER,
                'status': 'accepted'
            }
        ),
    }
}

schema_fixtures = {
    'member': {
        'GET': (
            {},
            {
                'name': 'member',
                'properties': {
                    'image_id': {},
                    'member_id': {}
                }
            },
        )
    }
}


class TestController(testtools.TestCase):
    def setUp(self):
        super(TestController, self).setUp()
        self.api = utils.FakeAPI(data_fixtures)
        self.schema_api = utils.FakeSchemaAPI(schema_fixtures)
        self.controller = base.BaseController(self.api, self.schema_api,
                                              image_members.Controller)

    def test_list_image_members(self):
        image_id = IMAGE
        image_members = self.controller.list(image_id)
        self.assertEqual(IMAGE, image_members[0].image_id)
        self.assertEqual(MEMBER, image_members[0].member_id)

    def test_delete_image_member(self):
        image_id = IMAGE
        member_id = MEMBER
        self.controller.delete(image_id, member_id)
        expect = [
            ('DELETE',
             '/v2/images/{image}/members/{mem}'.format(image=IMAGE,
                                                       mem=MEMBER),
             {},
             None)]
        self.assertEqual(expect, self.api.calls)

    def test_update_image_members(self):
        image_id = IMAGE
        member_id = MEMBER
        status = 'accepted'
        image_member = self.controller.update(image_id, member_id, status)
        self.assertEqual(IMAGE, image_member.image_id)
        self.assertEqual(MEMBER, image_member.member_id)
        self.assertEqual(status, image_member.status)

    def test_create_image_members(self):
        image_id = IMAGE
        member_id = MEMBER
        status = 'pending'
        image_member = self.controller.create(image_id, member_id)
        self.assertEqual(IMAGE, image_member.image_id)
        self.assertEqual(MEMBER, image_member.member_id)
        self.assertEqual(status, image_member.status)
