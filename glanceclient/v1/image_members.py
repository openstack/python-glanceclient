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

from glanceclient.common import base


class ImageMember(base.Resource):
    def __repr__(self):
        return "<ImageMember %s>" % self._info


class ImageMemberManager(base.Manager):
    resource_class = ImageMember

    def get(self, image, member_id):
        url = '/v1/images/%s' % (base.getid(image), member_id)
        return self._get(url, 'member')

    def list(self, image):
        url = '/v1/images/%s/members' % base.getid(image)
        return self._list(url, 'members')

    def delete(self, image, member):
        image_id = base.getid(image)
        try:
            member_id = base.getid(member)
        except AttributeError:
            member_id = member

        self._delete("/v1/images/%s/members/%s" % (image_id, member_id))

    def create(self, image, member_id, can_share=False):
        """Create an image"""
        url = '/v1/images/%s/members/%s' % (base.getid(image), member_id)
        body = {'member': {'can_share': can_share}}
        self._update(url, body=body)

    def replace(self, image, members):
        memberships = []
        for member in members:
            try:
                obj = {
                    'member_id': member.member_id,
                    'can_share': member.can_share,
                }
            except AttributeError:
                obj = {'member_id': member['member_id']}
                if 'can_share' in member:
                    obj['can_share'] = member['can_share']
            memberships.append(obj)
        url = '/v1/images/%s/members' % base.getid(image)
        self.api.put(url, {}, {'memberships': memberships})
