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

import warlock

from glanceclient.v2 import image_members
from tests import utils


IMAGE = '3a4560a1-e585-443e-9b39-553b46ec92d1'
MEMBER = '11223344-5566-7788-9911-223344556677'


fixtures = {
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
    },
}


fake_schema = {'name': 'member', 'properties': {'image_id': {},
                                                'member_id': {}}}
FakeModel = warlock.model_factory(fake_schema)


class TestController(testtools.TestCase):
    def setUp(self):
        super(TestController, self).setUp()
        self.api = utils.FakeAPI(fixtures)
        self.controller = image_members.Controller(self.api, FakeModel)

    def test_list_image_members(self):
        image_id = IMAGE
        #NOTE(iccha): cast to list since the controller returns a generator
        image_members = list(self.controller.list(image_id))
        self.assertEqual(image_members[0].image_id, IMAGE)
        self.assertEqual(image_members[0].member_id, MEMBER)

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
        self.assertEqual(self.api.calls, expect)

    def test_update_image_members(self):
        image_id = IMAGE
        member_id = MEMBER
        status = 'accepted'
        image_member = self.controller.update(image_id, member_id, status)
        self.assertEqual(image_member.image_id, IMAGE)
        self.assertEqual(image_member.member_id, MEMBER)
        self.assertEqual(image_member.status, status)

    def test_create_image_members(self):
        image_id = IMAGE
        member_id = MEMBER
        status = 'pending'
        image_member = self.controller.create(image_id, member_id)
        self.assertEqual(image_member.image_id, IMAGE)
        self.assertEqual(image_member.member_id, MEMBER)
        self.assertEqual(image_member.status, status)
