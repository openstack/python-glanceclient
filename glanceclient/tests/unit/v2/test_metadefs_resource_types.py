# Copyright 2012 OpenStack Foundation.
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
RESOURCE_TYPE1 = 'ResourceType1'
RESOURCE_TYPE2 = 'ResourceType2'
RESOURCE_TYPE3 = 'ResourceType3'
RESOURCE_TYPE4 = 'ResourceType4'
RESOURCE_TYPENEW = 'ResourceTypeNew'


data_fixtures = {
    "/v2/metadefs/namespaces/%s/resource_types" % NAMESPACE1: {
        "GET": (
            {},
            {
                "resource_type_associations": [
                    {
                        "name": RESOURCE_TYPE3,
                        "created_at": "2014-08-14T09:07:06Z",
                        "updated_at": "2014-08-14T09:07:06Z",
                    },
                    {
                        "name": RESOURCE_TYPE4,
                        "prefix": "PREFIX:",
                        "created_at": "2014-08-14T09:07:06Z",
                        "updated_at": "2014-08-14T09:07:06Z",
                    }
                ]
            }
        ),
        "POST": (
            {},
            {
                "name": RESOURCE_TYPENEW,
                "prefix": "PREFIX:",
                "created_at": "2014-08-14T09:07:06Z",
                "updated_at": "2014-08-14T09:07:06Z",
            }
        ),
    },
    "/v2/metadefs/namespaces/%s/resource_types/%s" % (NAMESPACE1,
                                                      RESOURCE_TYPE1):
    {
        "DELETE": (
            {},
            {}
        ),
    },
    "/v2/metadefs/resource_types": {
        "GET": (
            {},
            {
                "resource_types": [
                    {
                        "name": RESOURCE_TYPE1,
                        "created_at": "2014-08-14T09:07:06Z",
                        "updated_at": "2014-08-14T09:07:06Z",
                    },
                    {
                        "name": RESOURCE_TYPE2,
                        "created_at": "2014-08-14T09:07:06Z",
                        "updated_at": "2014-08-14T09:07:06Z",
                    }
                ]
            }
        )
    }
}

schema_fixtures = {
    "metadefs/resource_type": {
        "GET": (
            {},
            {
                "name": "resource_type",
                "properties": {
                    "prefix": {
                        "type": "string",
                        "description": "Specifies the prefix to use for the "
                                       "given resource type. Any properties "
                                       "in the namespace should be prefixed "
                                       "with this prefix when being applied "
                                       "to the specified resource type. Must "
                                       "include prefix separator (e.g. a "
                                       "colon :).",
                        "maxLength": 80
                    },
                    "properties_target": {
                        "type": "string",
                        "description": "Some resource types allow more than "
                                       "one key / value pair per instance.  "
                                       "For example, Cinder allows user and "
                                       "image metadata on volumes. Only the "
                                       "image properties metadata is "
                                       "evaluated by Nova (scheduling or "
                                       "drivers). This property allows a "
                                       "namespace target to remove the "
                                       "ambiguity.",
                        "maxLength": 80
                    },
                    "name": {
                        "type": "string",
                        "description": "Resource type names should be "
                                       "aligned with Heat resource types "
                                       "whenever possible: http://docs."
                                       "openstack.org/developer/heat/"
                                       "template_guide/openstack.html",
                        "maxLength": 80
                    },
                    "created_at": {
                        "type": "string",
                        "readOnly": True,
                        "description": "Date and time of resource type "
                                       "association",
                        "format": "date-time"
                    },
                    "updated_at": {
                        "type": "string",
                        "readOnly": True,
                        "description": "Date and time of the last resource "
                                       "type association modification ",
                        "format": "date-time"
                    },
                }
            }
        )
    }
}


class TestResoureTypeController(testtools.TestCase):
    def setUp(self):
        super(TestResoureTypeController, self).setUp()
        self.api = utils.FakeAPI(data_fixtures)
        self.schema_api = utils.FakeSchemaAPI(schema_fixtures)
        self.controller = base.BaseResourceTypeController(
            self.api, self.schema_api, metadefs.ResourceTypeController)

    def test_list_resource_types(self):
        resource_types = self.controller.list()
        names = [rt.name for rt in resource_types]
        self.assertEqual([RESOURCE_TYPE1, RESOURCE_TYPE2], names)

    def test_get_resource_types(self):
        resource_types = self.controller.get(NAMESPACE1)
        self.assertEqual([RESOURCE_TYPE3, RESOURCE_TYPE4], resource_types)

    def test_associate_resource_types(self):
        resource_types = self.controller.associate(NAMESPACE1,
                                                   name=RESOURCE_TYPENEW)

        self.assertEqual(RESOURCE_TYPENEW, resource_types['name'])

    def test_associate_resource_types_invalid_property(self):
        longer = '1234' * 50
        properties = {'name': RESOURCE_TYPENEW, 'prefix': longer}
        self.assertRaises(TypeError, self.controller.associate, NAMESPACE1,
                          **properties)

    def test_deassociate_resource_types(self):
        self.controller.deassociate(NAMESPACE1, RESOURCE_TYPE1)
        expect = [
            ('DELETE',
             '/v2/metadefs/namespaces/%s/resource_types/%s' % (NAMESPACE1,
                                                               RESOURCE_TYPE1),
             {},
             None)]
        self.assertEqual(expect, self.api.calls)
