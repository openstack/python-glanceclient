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
PROPERTY1 = 'Property1'
PROPERTY2 = 'Property2'
PROPERTYNEW = 'PropertyNew'

data_fixtures = {
    "/v2/metadefs/namespaces/%s/properties" % NAMESPACE1: {
        "GET": (
            {},
            {
                "properties": {
                    PROPERTY1: {
                        "default": "1",
                        "type": "integer",
                        "description": "Number of cores.",
                        "title": "cores"
                    },
                    PROPERTY2: {
                        "items": {
                            "enum": [
                                "Intel",
                                "AMD"
                            ],
                            "type": "string"
                        },
                        "type": "array",
                        "description": "Specifies the CPU manufacturer.",
                        "title": "Vendor"
                    },
                }
            }
        ),
        "POST": (
            {},
            {
                "items": {
                    "enum": [
                        "Intel",
                        "AMD"
                    ],
                    "type": "string"
                },
                "type": "array",
                "description": "UPDATED_DESCRIPTION",
                "title": "Vendor",
                "name": PROPERTYNEW
            }
        ),
        "DELETE": (
            {},
            {}
        )
    },
    "/v2/metadefs/namespaces/%s/properties/%s" % (NAMESPACE1, PROPERTY1): {
        "GET": (
            {},
            {
                "items": {
                    "enum": [
                        "Intel",
                        "AMD"
                    ],
                    "type": "string"
                },
                "type": "array",
                "description": "Specifies the CPU manufacturer.",
                "title": "Vendor"
            }
        ),
        "PUT": (
            {},
            {
                "items": {
                    "enum": [
                        "Intel",
                        "AMD"
                    ],
                    "type": "string"
                },
                "type": "array",
                "description": "UPDATED_DESCRIPTION",
                "title": "Vendor"
            }
        ),
        "DELETE": (
            {},
            {}
        )
    }
}

schema_fixtures = {
    "metadefs/property": {
        "GET": (
            {},
            {
                "additionalProperties": False,
                "definitions": {
                    "positiveIntegerDefault0": {
                        "allOf": [
                            {
                                "$ref": "#/definitions/positiveInteger"
                            },
                            {
                                "default": 0
                            }
                        ]
                    },
                    "stringArray": {
                        "minItems": 1,
                        "items": {
                            "type": "string"
                        },
                        "uniqueItems": True,
                        "type": "array"
                    },
                    "positiveInteger": {
                        "minimum": 0,
                        "type": "integer"
                    }
                },
                "required": [
                    "name",
                    "title",
                    "type"
                ],
                "name": "property",
                "properties": {
                    "description": {
                        "type": "string"
                    },
                    "minLength": {
                        "$ref": "#/definitions/positiveIntegerDefault0"
                    },
                    "enum": {
                        "type": "array"
                    },
                    "minimum": {
                        "type": "number"
                    },
                    "maxItems": {
                        "$ref": "#/definitions/positiveInteger"
                    },
                    "maxLength": {
                        "$ref": "#/definitions/positiveInteger"
                    },
                    "uniqueItems": {
                        "default": False,
                        "type": "boolean"
                    },
                    "additionalItems": {
                        "type": "boolean"
                    },
                    "name": {
                        "type": "string"
                    },
                    "title": {
                        "type": "string"
                    },
                    "default": {},
                    "pattern": {
                        "type": "string",
                        "format": "regex"
                    },
                    "required": {
                        "$ref": "#/definitions/stringArray"
                    },
                    "maximum": {
                        "type": "number"
                    },
                    "minItems": {
                        "$ref": "#/definitions/positiveIntegerDefault0"
                    },
                    "readonly": {
                        "type": "boolean"
                    },
                    "items": {
                        "type": "object",
                        "properties": {
                            "enum": {
                                "type": "array"
                            },
                            "type": {
                                "enum": [
                                    "array",
                                    "boolean",
                                    "integer",
                                    "number",
                                    "object",
                                    "string",
                                    "null"
                                ],
                                "type": "string"
                            }
                        }
                    },
                    "type": {
                        "enum": [
                            "array",
                            "boolean",
                            "integer",
                            "number",
                            "object",
                            "string",
                            "null"
                        ],
                        "type": "string"
                    }
                }
            }
        )
    }
}


class TestPropertyController(testtools.TestCase):
    def setUp(self):
        super(TestPropertyController, self).setUp()
        self.api = utils.FakeAPI(data_fixtures)
        self.schema_api = utils.FakeSchemaAPI(schema_fixtures)
        self.controller = base.BaseController(self.api, self.schema_api,
                                              metadefs.PropertyController)

    def test_list_property(self):
        properties = self.controller.list(NAMESPACE1)
        actual = [prop.name for prop in properties]
        self.assertEqual(sorted([PROPERTY1, PROPERTY2]), sorted(actual))

    def test_get_property(self):
        prop = self.controller.get(NAMESPACE1, PROPERTY1)
        self.assertEqual(PROPERTY1, prop.name)

    def test_create_property(self):
        properties = {
            'name': PROPERTYNEW,
            'title': 'TITLE',
            'type': 'string'
        }
        obj = self.controller.create(NAMESPACE1, **properties)
        self.assertEqual(PROPERTYNEW, obj.name)

    def test_create_property_invalid_property(self):
        properties = {
            'namespace': NAMESPACE1
        }
        self.assertRaises(TypeError, self.controller.create, **properties)

    def test_update_property(self):
        properties = {
            'description': 'UPDATED_DESCRIPTION'
        }
        prop = self.controller.update(NAMESPACE1, PROPERTY1, **properties)
        self.assertEqual(PROPERTY1, prop.name)

    def test_update_property_invalid_property(self):
        properties = {
            'type': 'INVALID'
        }
        self.assertRaises(TypeError, self.controller.update, NAMESPACE1,
                          PROPERTY1, **properties)

    def test_update_property_disallowed_fields(self):
        properties = {
            'description': 'UPDATED_DESCRIPTION'
        }
        self.controller.update(NAMESPACE1, PROPERTY1, **properties)
        actual = self.api.calls
        _disallowed_fields = ['created_at', 'updated_at']
        for key in actual[1][3]:
            self.assertNotIn(key, _disallowed_fields)

    def test_delete_property(self):
        self.controller.delete(NAMESPACE1, PROPERTY1)
        expect = [
            ('DELETE',
             '/v2/metadefs/namespaces/%s/properties/%s' % (NAMESPACE1,
                                                           PROPERTY1),
             {},
             None)]
        self.assertEqual(expect, self.api.calls)

    def test_delete_all_properties(self):
        self.controller.delete_all(NAMESPACE1)
        expect = [
            ('DELETE',
             '/v2/metadefs/namespaces/%s/properties' % NAMESPACE1,
             {},
             None)]
        self.assertEqual(expect, self.api.calls)
