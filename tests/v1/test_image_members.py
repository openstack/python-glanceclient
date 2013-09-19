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

import testtools

import glanceclient.v1.images
import glanceclient.v1.image_members
from tests import utils


fixtures = {
    '/v1/images/1/members': {
        'GET': (
            {},
            {'members': [
                {'member_id': '1', 'can_share': False},
            ]},
        ),
        'PUT': ({}, None),
    },
    '/v1/images/1/members/1': {
        'GET': (
            {},
            {'member': {
                'member_id': '1',
                'can_share': False,
            }},
        ),
        'PUT': ({}, None),
        'DELETE': ({}, None),
    },
    '/v1/shared-images/1': {
        'GET': (
            {},
            {'shared_images': [
                {'image_id': '1', 'can_share': False},
            ]},
        ),
    },
}


class ImageMemberManagerTest(testtools.TestCase):

    def setUp(self):
        super(ImageMemberManagerTest, self).setUp()
        self.api = utils.FakeAPI(fixtures)
        self.mgr = glanceclient.v1.image_members.ImageMemberManager(self.api)
        self.image = glanceclient.v1.images.Image(self.api, {'id': '1'}, True)

    def test_list_by_image(self):
        members = self.mgr.list(image=self.image)
        expect = [('GET', '/v1/images/1/members', {}, None)]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].member_id, '1')
        self.assertEqual(members[0].image_id, '1')
        self.assertEqual(members[0].can_share, False)

    def test_list_by_member(self):
        resource_class = glanceclient.v1.image_members.ImageMember
        member = resource_class(self.api, {'member_id': '1'}, True)
        self.mgr.list(member=member)
        expect = [('GET', '/v1/shared-images/1', {}, None)]
        self.assertEqual(self.api.calls, expect)

    def test_get(self):
        member = self.mgr.get(self.image, '1')
        expect = [('GET', '/v1/images/1/members/1', {}, None)]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(member.member_id, '1')
        self.assertEqual(member.image_id, '1')
        self.assertEqual(member.can_share, False)

    def test_delete(self):
        self.mgr.delete('1', '1')
        expect = [('DELETE', '/v1/images/1/members/1', {}, None)]
        self.assertEqual(self.api.calls, expect)

    def test_create(self):
        self.mgr.create(self.image, '1', can_share=True)
        expect_body = {'member': {'can_share': True}}
        expect = [('PUT', '/v1/images/1/members/1', {}, expect_body)]
        self.assertEqual(self.api.calls, expect)

    def test_replace(self):
        body = [
            {'member_id': '2', 'can_share': False},
            {'member_id': '3'},
        ]
        self.mgr.replace(self.image, body)
        expect = [('PUT', '/v1/images/1/members', {}, {'memberships': body})]
        self.assertEqual(self.api.calls, expect)

    def test_replace_objects(self):
        body = [
            glanceclient.v1.image_members.ImageMember(
                self.mgr, {'member_id': '2', 'can_share': False}, True),
            glanceclient.v1.image_members.ImageMember(
                self.mgr, {'member_id': '3', 'can_share': True}, True),
        ]
        self.mgr.replace(self.image, body)
        expect_body = {
            'memberships': [
                {'member_id': '2', 'can_share': False},
                {'member_id': '3', 'can_share': True},
            ],
        }
        expect = [('PUT', '/v1/images/1/members', {}, expect_body)]
        self.assertEqual(self.api.calls, expect)
