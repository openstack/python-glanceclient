# Copyright 2015 OpenStack Foundation.
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
from glanceclient.v2 import metadefs

NAMESPACE1 = 'Namespace1'
TAG1 = 'Tag1'
TAG2 = 'Tag2'
TAGNEW1 = 'TagNew1'
TAGNEW2 = 'TagNew2'
TAGNEW3 = 'TagNew3'


def _get_tag_fixture(tag_name, **kwargs):
    tag = {
        "name": tag_name
    }
    tag.update(kwargs)
    return tag


data_fixtures = {
    "/v2/metadefs/namespaces/%s/tags" % NAMESPACE1: {
        "GET": (
            {},
            {
                "tags": [
                    _get_tag_fixture(TAG1),
                    _get_tag_fixture(TAG2)
                ]
            }
        ),
        "POST": (
            {},
            {
                'tags': [
                    _get_tag_fixture(TAGNEW2),
                    _get_tag_fixture(TAGNEW3)
                ]
            }
        ),
        "DELETE": (
            {},
            {}
        )
    },
    "/v2/metadefs/namespaces/%s/tags/%s" % (NAMESPACE1, TAGNEW1): {
        "POST": (
            {},
            _get_tag_fixture(TAGNEW1)
        )
    },
    "/v2/metadefs/namespaces/%s/tags/%s" % (NAMESPACE1, TAG1): {
        "GET": (
            {},
            _get_tag_fixture(TAG1)
        ),
        "PUT": (
            {},
            _get_tag_fixture(TAG2)
        ),
        "DELETE": (
            {},
            {}
        )
    },
    "/v2/metadefs/namespaces/%s/tags/%s" % (NAMESPACE1, TAG2): {
        "GET": (
            {},
            _get_tag_fixture(TAG2)
        ),
    },
    "/v2/metadefs/namespaces/%s/tags/%s" % (NAMESPACE1, TAGNEW2): {
        "GET": (
            {},
            _get_tag_fixture(TAGNEW2)
        ),
    },
    "/v2/metadefs/namespaces/%s/tags/%s" % (NAMESPACE1, TAGNEW3): {
        "GET": (
            {},
            _get_tag_fixture(TAGNEW3)
        ),
    }

}

schema_fixtures = {
    "metadefs/tag": {
        "GET": (
            {},
            {
                "additionalProperties": True,
                "name": {
                    "type": "string"
                },
                "created_at": {
                    "type": "string",
                    "readOnly": True,
                    "description": ("Date and time of tag creation"),
                    "format": "date-time"
                },
                "updated_at": {
                    "type": "string",
                    "readOnly": True,
                    "description": ("Date and time of the last tag"
                                    "  modification"),
                    "format": "date-time"
                },
                'properties': {}
            }
        )
    }
}


class TestTagController(testtools.TestCase):
    def setUp(self):
        super(TestTagController, self).setUp()
        self.api = utils.FakeAPI(data_fixtures)
        self.schema_api = utils.FakeSchemaAPI(schema_fixtures)
        self.controller = base.BaseController(self.api, self.schema_api,
                                              metadefs.TagController)

    def test_list_tag(self):
        tags = self.controller.list(NAMESPACE1)
        actual = [tag.name for tag in tags]
        self.assertEqual([TAG1, TAG2], actual)

    def test_get_tag(self):
        tag = self.controller.get(NAMESPACE1, TAG1)
        self.assertEqual(TAG1, tag.name)

    def test_create_tag(self):
        tag = self.controller.create(NAMESPACE1, TAGNEW1)
        self.assertEqual(TAGNEW1, tag.name)

    def test_create_multiple_tags(self):
        properties = {
            'tags': [TAGNEW2, TAGNEW3]
        }
        tags = self.controller.create_multiple(NAMESPACE1, **properties)
        self.assertEqual([TAGNEW2, TAGNEW3], tags)

    def test_update_tag(self):
        properties = {
            'name': TAG2
        }
        tag = self.controller.update(NAMESPACE1, TAG1, **properties)
        self.assertEqual(TAG2, tag.name)

    def test_delete_tag(self):
        self.controller.delete(NAMESPACE1, TAG1)
        expect = [
            ('DELETE',
             '/v2/metadefs/namespaces/%s/tags/%s' % (NAMESPACE1, TAG1),
             {},
             None)]
        self.assertEqual(expect, self.api.calls)

    def test_delete_all_tags(self):
        self.controller.delete_all(NAMESPACE1)
        expect = [
            ('DELETE',
             '/v2/metadefs/namespaces/%s/tags' % NAMESPACE1,
             {},
             None)]
        self.assertEqual(expect, self.api.calls)
