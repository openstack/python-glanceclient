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
OBJECT1 = 'Object1'
OBJECT2 = 'Object2'
OBJECTNEW = 'ObjectNew'
PROPERTY1 = 'Property1'
PROPERTY2 = 'Property2'
PROPERTY3 = 'Property3'
PROPERTY4 = 'Property4'


def _get_object_fixture(ns_name, obj_name, **kwargs):
    obj = {
        "description": "DESCRIPTION",
        "name": obj_name,
        "self": "/v2/metadefs/namespaces/%s/objects/%s" %
                (ns_name, obj_name),
        "required": [],
        "properties": {
            PROPERTY1: {
                "type": "integer",
                "description": "DESCRIPTION",
                "title": "Quota: CPU Shares"
            },
            PROPERTY2: {
                "minimum": 1000,
                "type": "integer",
                "description": "DESCRIPTION",
                "maximum": 1000000,
                "title": "Quota: CPU Period"
            }},
        "schema": "/v2/schemas/metadefs/object",
        "created_at": "2014-08-14T09:07:06Z",
        "updated_at": "2014-08-14T09:07:06Z",
    }

    obj.update(kwargs)

    return obj


data_fixtures = {
    "/v2/metadefs/namespaces/%s/objects" % NAMESPACE1: {
        "GET": (
            {},
            {
                "objects": [
                    _get_object_fixture(NAMESPACE1, OBJECT1),
                    _get_object_fixture(NAMESPACE1, OBJECT2)
                ],
                "schema": "v2/schemas/metadefs/objects"
            }
        ),
        "POST": (
            {},
            _get_object_fixture(NAMESPACE1, OBJECTNEW)
        ),
        "DELETE": (
            {},
            {}
        )
    },
    "/v2/metadefs/namespaces/%s/objects/%s" % (NAMESPACE1, OBJECT1): {
        "GET": (
            {},
            _get_object_fixture(NAMESPACE1, OBJECT1)
        ),
        "PUT": (
            {},
            _get_object_fixture(NAMESPACE1, OBJECT1)
        ),
        "DELETE": (
            {},
            {}
        )
    }
}

schema_fixtures = {
    "metadefs/object": {
        "GET": (
            {},
            {
                "additionalProperties": False,
                "definitions": {
                    "property": {
                        "additionalProperties": {
                            "required": [
                                "title",
                                "type"
                            ],
                            "type": "object",
                            "properties": {
                                "additionalItems": {
                                    "type": "boolean"
                                },
                                "enum": {
                                    "type": "array"
                                },
                                "description": {
                                    "type": "string"
                                },
                                "title": {
                                    "type": "string"
                                },
                                "default": {},
                                "minLength": {
                                    "$ref": "#/definitions/positiveInteger"
                                            "Default0"
                                },
                                "required": {
                                    "$ref": "#/definitions/stringArray"
                                },
                                "maximum": {
                                    "type": "number"
                                },
                                "minItems": {
                                    "$ref": "#/definitions/positiveInteger"
                                            "Default0"
                                },
                                "readonly": {
                                    "type": "boolean"
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
                                "pattern": {
                                    "type": "string",
                                    "format": "regex"
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
                        },
                        "type": "object"
                    },
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
                        "uniqueItems": True,
                        "items": {
                            "type": "string"
                        },
                        "type": "array"
                    },
                    "positiveInteger": {
                        "minimum": 0,
                        "type": "integer"
                    }
                },
                "required": [
                    "name"
                ],
                "name": "object",
                "properties": {
                    "created_at": {
                        "type": "string",
                        "readOnly": True,
                        "description": "Date and time of object creation ",
                        "format": "date-time"
                    },
                    "description": {
                        "type": "string"
                    },
                    "name": {
                        "type": "string"
                    },
                    "self": {
                        "type": "string"
                    },
                    "required": {
                        "$ref": "#/definitions/stringArray"
                    },
                    "properties": {
                        "$ref": "#/definitions/property"
                    },
                    "schema": {
                        "type": "string"
                    },
                    "updated_at": {
                        "type": "string",
                        "readOnly": True,
                        "description": "Date and time of the last object "
                                       "modification",
                        "format": "date-time"
                    },
                }
            }
        )
    }
}


class TestObjectController(testtools.TestCase):
    def setUp(self):
        super(TestObjectController, self).setUp()
        self.api = utils.FakeAPI(data_fixtures)
        self.schema_api = utils.FakeSchemaAPI(schema_fixtures)
        self.controller = base.BaseController(self.api, self.schema_api,
                                              metadefs.ObjectController)

    def test_list_object(self):
        objects = self.controller.list(NAMESPACE1)
        actual = [obj.name for obj in objects]
        self.assertEqual([OBJECT1, OBJECT2], actual)

    def test_get_object(self):
        obj = self.controller.get(NAMESPACE1, OBJECT1)
        self.assertEqual(OBJECT1, obj.name)
        self.assertEqual(sorted([PROPERTY1, PROPERTY2]),
                         sorted(list(obj.properties.keys())))

    def test_create_object(self):
        properties = {
            'name': OBJECTNEW,
            'description': 'DESCRIPTION'
        }
        obj = self.controller.create(NAMESPACE1, **properties)
        self.assertEqual(OBJECTNEW, obj.name)

    def test_create_object_invalid_property(self):
        properties = {
            'namespace': NAMESPACE1
        }
        self.assertRaises(TypeError, self.controller.create, **properties)

    def test_update_object(self):
        properties = {
            'description': 'UPDATED_DESCRIPTION'
        }
        obj = self.controller.update(NAMESPACE1, OBJECT1, **properties)
        self.assertEqual(OBJECT1, obj.name)

    def test_update_object_invalid_property(self):
        properties = {
            'required': 'INVALID'
        }
        self.assertRaises(TypeError, self.controller.update, NAMESPACE1,
                          OBJECT1, **properties)

    def test_update_object_disallowed_fields(self):
        properties = {
            'description': 'UPDATED_DESCRIPTION'
        }
        self.controller.update(NAMESPACE1, OBJECT1, **properties)
        actual = self.api.calls
        # API makes three calls(GET, PUT, GET) for object update.
        # PUT has the request body in the list
        '''('PUT', '/v2/metadefs/namespaces/Namespace1/objects/Object1', {},
        [('description', 'UPDATED_DESCRIPTION'),
        ('name', 'Object1'),
        ('properties', ...),
        ('required', [])])'''

        _disallowed_fields = ['self', 'schema', 'created_at', 'updated_at']
        for key in actual[1][3]:
            self.assertNotIn(key, _disallowed_fields)

    def test_delete_object(self):
        self.controller.delete(NAMESPACE1, OBJECT1)
        expect = [
            ('DELETE',
             '/v2/metadefs/namespaces/%s/objects/%s' % (NAMESPACE1, OBJECT1),
             {},
             None)]
        self.assertEqual(expect, self.api.calls)

    def test_delete_all_objects(self):
        self.controller.delete_all(NAMESPACE1)
        expect = [
            ('DELETE',
             '/v2/metadefs/namespaces/%s/objects' % NAMESPACE1,
             {},
             None)]
        self.assertEqual(expect, self.api.calls)
