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

from glanceclient.tests import utils
import glanceclient.v1.image_members
import glanceclient.v1.images


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
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(1, len(members))
        self.assertEqual('1', members[0].member_id)
        self.assertEqual('1', members[0].image_id)
        self.assertEqual(False, members[0].can_share)

    def test_list_by_member(self):
        resource_class = glanceclient.v1.image_members.ImageMember
        member = resource_class(self.api, {'member_id': '1'}, True)
        self.mgr.list(member=member)
        expect = [('GET', '/v1/shared-images/1', {}, None)]
        self.assertEqual(expect, self.api.calls)

    def test_get(self):
        member = self.mgr.get(self.image, '1')
        expect = [('GET', '/v1/images/1/members/1', {}, None)]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual('1', member.member_id)
        self.assertEqual('1', member.image_id)
        self.assertEqual(False, member.can_share)

    def test_delete(self):
        self.mgr.delete('1', '1')
        expect = [('DELETE', '/v1/images/1/members/1', {}, None)]
        self.assertEqual(expect, self.api.calls)

    def test_create(self):
        self.mgr.create(self.image, '1', can_share=True)
        expect_body = {'member': {'can_share': True}}
        expect = [('PUT', '/v1/images/1/members/1', {},
                   sorted(expect_body.items()))]
        self.assertEqual(expect, self.api.calls)

    def test_replace(self):
        body = [
            {'member_id': '2', 'can_share': False},
            {'member_id': '3'},
        ]
        self.mgr.replace(self.image, body)
        expect = [('PUT', '/v1/images/1/members', {},
                   sorted({'memberships': body}.items()))]
        self.assertEqual(expect, self.api.calls)

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
        expect = [('PUT', '/v1/images/1/members', {},
                   sorted(expect_body.items()))]
        self.assertEqual(expect, self.api.calls)
