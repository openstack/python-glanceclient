
import unittest

from tests.v1 import utils

import glanceclient.v1.images
import glanceclient.v1.image_members


class ImageMemberManagerTest(unittest.TestCase):

    def setUp(self):
        self.api = utils.FakeAPI()
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
        members = self.mgr.list(member='1')
        expect = [('GET', '/v1/shared-images/1', {}, None)]
        self.assertEqual(self.api.calls, expect)
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].member_id, '1')
        self.assertEqual(members[0].image_id, '1')
        self.assertEqual(members[0].can_share, False)

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
                self.mgr, {'member_id': '2', 'can_share': False}),
            glanceclient.v1.image_members.ImageMember(
                self.mgr, {'member_id': '3', 'can_share': True}),
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
