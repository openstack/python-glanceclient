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

DEFAULT_PAGE_SIZE = 20
NAMESPACE1 = 'Namespace1'
NAMESPACE2 = 'Namespace2'
NAMESPACE3 = 'Namespace3'
NAMESPACE4 = 'Namespace4'
NAMESPACE5 = 'Namespace5'
NAMESPACE6 = 'Namespace6'
NAMESPACE7 = 'Namespace7'
NAMESPACE8 = 'Namespace8'
NAMESPACENEW = 'NamespaceNew'
RESOURCE_TYPE1 = 'ResourceType1'
RESOURCE_TYPE2 = 'ResourceType2'
OBJECT1 = 'Object1'
PROPERTY1 = 'Property1'
PROPERTY2 = 'Property2'


def _get_namespace_fixture(ns_name, rt_name=RESOURCE_TYPE1, **kwargs):
    ns = {
        "display_name": "Flavor Quota",
        "description": "DESCRIPTION1",
        "self": "/v2/metadefs/namespaces/%s" % ns_name,
        "namespace": ns_name,
        "visibility": "public",
        "protected": True,
        "owner": "admin",
        "resource_types": [
            {
                "name": rt_name
            }
        ],
        "schema": "/v2/schemas/metadefs/namespace",
        "created_at": "2014-08-14T09:07:06Z",
        "updated_at": "2014-08-14T09:07:06Z",
    }

    ns.update(kwargs)

    return ns


data_fixtures = {
    f"/v2/metadefs/namespaces?limit={DEFAULT_PAGE_SIZE}": {
        "GET": (
            {},
            {
                "first": "/v2/metadefs/namespaces?limit=20",
                "namespaces": [
                    _get_namespace_fixture(NAMESPACE1),
                    _get_namespace_fixture(NAMESPACE2),
                ],
                "schema": "/v2/schemas/metadefs/namespaces"
            }
        )
    },
    "/v2/metadefs/namespaces?limit=1": {
        "GET": (
            {},
            {
                "first": "/v2/metadefs/namespaces?limit=1",
                "namespaces": [
                    _get_namespace_fixture(NAMESPACE7),
                ],
                "schema": "/v2/schemas/metadefs/namespaces",
                "next": "/v2/metadefs/namespaces?marker=%s&limit=1"
                        % NAMESPACE7,
            }
        )
    },
    "/v2/metadefs/namespaces?limit=1&marker=%s" % NAMESPACE7: {
        "GET": (
            {},
            {
                "first": "/v2/metadefs/namespaces?limit=2",
                "namespaces": [
                    _get_namespace_fixture(NAMESPACE8),
                ],
                "schema": "/v2/schemas/metadefs/namespaces"
            }
        )
    },
    "/v2/metadefs/namespaces?limit=2&marker=%s" % NAMESPACE6: {
        "GET": (
            {},
            {
                "first": "/v2/metadefs/namespaces?limit=2",
                "namespaces": [
                    _get_namespace_fixture(NAMESPACE7),
                    _get_namespace_fixture(NAMESPACE8),
                ],
                "schema": "/v2/schemas/metadefs/namespaces"
            }
        )
    },
    f"/v2/metadefs/namespaces?limit={DEFAULT_PAGE_SIZE}&sort_dir=asc": {
        "GET": (
            {},
            {
                "first": "/v2/metadefs/namespaces?limit=1",
                "namespaces": [
                    _get_namespace_fixture(NAMESPACE1),
                ],
                "schema": "/v2/schemas/metadefs/namespaces"
            }
        )
    },
    f"/v2/metadefs/namespaces?limit={DEFAULT_PAGE_SIZE}&sort_key=created_at": {
        "GET": (
            {},
            {
                "first": "/v2/metadefs/namespaces?limit=1",
                "namespaces": [
                    _get_namespace_fixture(NAMESPACE1),
                ],
                "schema": "/v2/schemas/metadefs/namespaces"
            }
        )
    },
    "/v2/metadefs/namespaces?limit=%d&resource_types=%s" % (
        DEFAULT_PAGE_SIZE, RESOURCE_TYPE1): {
        "GET": (
            {},
            {
                "first": "/v2/metadefs/namespaces?limit=20",
                "namespaces": [
                    _get_namespace_fixture(NAMESPACE3),
                ],
                "schema": "/v2/schemas/metadefs/namespaces"
            }
        )
    },
    "/v2/metadefs/namespaces?limit=%d&resource_types="
    "%s%%2C%s" % (DEFAULT_PAGE_SIZE, RESOURCE_TYPE1, RESOURCE_TYPE2): {
        "GET": (
            {},
            {
                "first": "/v2/metadefs/namespaces?limit=20",
                "namespaces": [
                    _get_namespace_fixture(NAMESPACE4),
                ],
                "schema": "/v2/schemas/metadefs/namespaces"
            }
        )
    },
    f"/v2/metadefs/namespaces?limit={DEFAULT_PAGE_SIZE}&visibility=private": {
        "GET": (
            {},
            {
                "first": "/v2/metadefs/namespaces?limit=20",
                "namespaces": [
                    _get_namespace_fixture(NAMESPACE5),
                ],
                "schema": "/v2/schemas/metadefs/namespaces"
            }
        )
    },
    "/v2/metadefs/namespaces": {
        "POST": (
            {},
            {
                "display_name": "Flavor Quota",
                "description": "DESCRIPTION1",
                "self": "/v2/metadefs/namespaces/%s" % 'NamespaceNew',
                "namespace": 'NamespaceNew',
                "visibility": "public",
                "protected": True,
                "owner": "admin",
                "schema": "/v2/schemas/metadefs/namespace",
                "created_at": "2014-08-14T09:07:06Z",
                "updated_at": "2014-08-14T09:07:06Z",
            }
        )
    },
    "/v2/metadefs/namespaces/%s" % NAMESPACE1: {
        "GET": (
            {},
            {
                "display_name": "Flavor Quota",
                "description": "DESCRIPTION1",
                "objects": [
                    {
                        "description": "DESCRIPTION2",
                        "name": "OBJECT1",
                        "self": "/v2/metadefs/namespaces/%s/objects/" %
                                OBJECT1,
                        "required": [],
                        "properties": {
                            PROPERTY1: {
                                "type": "integer",
                                "description": "DESCRIPTION3",
                                "title": "Quota: CPU Shares"
                            },
                            PROPERTY2: {
                                "minimum": 1000,
                                "type": "integer",
                                "description": "DESCRIPTION4",
                                "maximum": 1000000,
                                "title": "Quota: CPU Period"
                            },
                        },
                        "schema": "/v2/schemas/metadefs/object"
                    }
                ],
                "self": "/v2/metadefs/namespaces/%s" % NAMESPACE1,
                "namespace": NAMESPACE1,
                "visibility": "public",
                "protected": True,
                "owner": "admin",
                "resource_types": [
                    {
                        "name": RESOURCE_TYPE1
                    }
                ],
                "schema": "/v2/schemas/metadefs/namespace",
                "created_at": "2014-08-14T09:07:06Z",
                "updated_at": "2014-08-14T09:07:06Z",
            }
        ),
        "PUT": (
            {},
            {
                "display_name": "Flavor Quota",
                "description": "DESCRIPTION1",
                "objects": [
                    {
                        "description": "DESCRIPTION2",
                        "name": "OBJECT1",
                        "self": "/v2/metadefs/namespaces/%s/objects/" %
                                OBJECT1,
                        "required": [],
                        "properties": {
                            PROPERTY1: {
                                "type": "integer",
                                "description": "DESCRIPTION3",
                                "title": "Quota: CPU Shares"
                            },
                            PROPERTY2: {
                                "minimum": 1000,
                                "type": "integer",
                                "description": "DESCRIPTION4",
                                "maximum": 1000000,
                                "title": "Quota: CPU Period"
                            },
                        },
                        "schema": "/v2/schemas/metadefs/object"
                    }
                ],
                "self": "/v2/metadefs/namespaces/%s" % NAMESPACENEW,
                "namespace": NAMESPACENEW,
                "visibility": "public",
                "protected": True,
                "owner": "admin",
                "resource_types": [
                    {
                        "name": RESOURCE_TYPE1
                    }
                ],
                "schema": "/v2/schemas/metadefs/namespace",
                "created_at": "2014-08-14T09:07:06Z",
                "updated_at": "2014-08-14T09:07:06Z",
            }
        ),
        "DELETE": (
            {},
            {}
        )
    },
    "/v2/metadefs/namespaces/%s?resource_type=%s" % (NAMESPACE6,
                                                     RESOURCE_TYPE1):
    {
        "GET": (
            {},
            {
                "display_name": "Flavor Quota",
                "description": "DESCRIPTION1",
                "objects": [],
                "self": "/v2/metadefs/namespaces/%s" % NAMESPACE1,
                "namespace": NAMESPACE6,
                "visibility": "public",
                "protected": True,
                "owner": "admin",
                "resource_types": [
                    {
                        "name": RESOURCE_TYPE1
                    }
                ],
                "schema": "/v2/schemas/metadefs/namespace",
                "created_at": "2014-08-14T09:07:06Z",
                "updated_at": "2014-08-14T09:07:06Z",
            }
        ),
    },
}

schema_fixtures = {
    "metadefs/namespace":
    {
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
                                    "$ref": "#/definitions/"
                                            "positiveIntegerDefault0"
                                },
                                "required": {
                                    "$ref": "#/definitions/stringArray"
                                },
                                "maximum": {
                                    "type": "number"
                                },
                                "minItems": {
                                    "$ref": "#/definitions/"
                                            "positiveIntegerDefault0"
                                },
                                "readonly": {
                                    "type": "boolean"
                                },
                                "minimum": {
                                    "type": "number"
                                },
                                "maxItems": {
                                    "$ref": "#/definitions/"
                                            "positiveInteger"
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
                    "namespace"
                ],
                "name": "namespace",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Provides a user friendly description "
                                       "of the namespace.",
                        "maxLength": 500
                    },
                    "updated_at": {
                        "type": "string",
                        "readOnly": True,
                        "description": "Date and time of the last namespace "
                                       "modification",
                        "format": "date-time"
                    },
                    "visibility": {
                        "enum": [
                            "public",
                            "private"
                        ],
                        "type": "string",
                        "description": "Scope of namespace accessibility."
                    },
                    "self": {
                        "type": "string"
                    },
                    "objects": {
                        "items": {
                            "type": "object",
                            "properties": {
                                "properties": {
                                    "$ref": "#/definitions/property"
                                },
                                "required": {
                                    "$ref": "#/definitions/stringArray"
                                },
                                "name": {
                                    "type": "string"
                                },
                                "description": {
                                    "type": "string"
                                }
                            }
                        },
                        "type": "array"
                    },
                    "owner": {
                        "type": "string",
                        "description": "Owner of the namespace.",
                        "maxLength": 255
                    },
                    "resource_types": {
                        "items": {
                            "type": "object",
                            "properties": {
                                "prefix": {
                                    "type": "string"
                                },
                                "name": {
                                    "type": "string"
                                },
                                "metadata_type": {
                                    "type": "string"
                                }
                            }
                        },
                        "type": "array"
                    },
                    "properties": {
                        "$ref": "#/definitions/property"
                    },
                    "display_name": {
                        "type": "string",
                        "description": "The user friendly name for the "
                                       "namespace. Used by UI if available.",
                        "maxLength": 80
                    },
                    "created_at": {
                        "type": "string",
                        "readOnly": True,
                        "description": "Date and time of namespace creation ",
                        "format": "date-time"
                    },
                    "namespace": {
                        "type": "string",
                        "description": "The unique namespace text.",
                        "maxLength": 80
                    },
                    "protected": {
                        "type": "boolean",
                        "description": "If true, namespace will not be "
                                       "deletable."
                    },
                    "schema": {
                        "type": "string"
                    }
                }
            }
        ),
    }
}


class TestNamespaceController(testtools.TestCase):
    def setUp(self):
        super(TestNamespaceController, self).setUp()
        self.api = utils.FakeAPI(data_fixtures)
        self.schema_api = utils.FakeSchemaAPI(schema_fixtures)
        self.controller = base.BaseController(self.api, self.schema_api,
                                              metadefs.NamespaceController)

    def test_list_namespaces(self):
        namespaces = self.controller.list()
        self.assertEqual(2, len(namespaces))
        self.assertEqual(NAMESPACE1, namespaces[0]['namespace'])
        self.assertEqual(NAMESPACE2, namespaces[1]['namespace'])

    def test_list_namespaces_paginate(self):
        namespaces = self.controller.list(page_size=1)
        self.assertEqual(2, len(namespaces))
        self.assertEqual(NAMESPACE7, namespaces[0]['namespace'])
        self.assertEqual(NAMESPACE8, namespaces[1]['namespace'])

    def test_list_with_limit_greater_than_page_size(self):
        namespaces = self.controller.list(page_size=1, limit=2)
        self.assertEqual(2, len(namespaces))
        self.assertEqual(NAMESPACE7, namespaces[0]['namespace'])
        self.assertEqual(NAMESPACE8, namespaces[1]['namespace'])

    def test_list_with_marker(self):
        namespaces = self.controller.list(marker=NAMESPACE6, page_size=2)
        self.assertEqual(2, len(namespaces))
        self.assertEqual(NAMESPACE7, namespaces[0]['namespace'])
        self.assertEqual(NAMESPACE8, namespaces[1]['namespace'])

    def test_list_with_sort_dir(self):
        namespaces = self.controller.list(sort_dir='asc', limit=1)
        self.assertEqual(1, len(namespaces))
        self.assertEqual(NAMESPACE1, namespaces[0]['namespace'])

    def test_list_with_sort_dir_invalid(self):
        # NOTE(TravT): The clients work by returning an iterator.
        # Invoking the iterator is what actually executes the logic.
        self.assertRaises(ValueError, self.controller.list, sort_dir='foo')

    def test_list_with_sort_key(self):
        namespaces = self.controller.list(sort_key='created_at', limit=1)
        self.assertEqual(1, len(namespaces))
        self.assertEqual(NAMESPACE1, namespaces[0]['namespace'])

    def test_list_with_sort_key_invalid(self):
        # NOTE(TravT): The clients work by returning an iterator.
        # Invoking the iterator is what actually executes the logic.
        self.assertRaises(ValueError, self.controller.list, sort_key='foo')

    def test_list_namespaces_with_one_resource_type_filter(self):
        namespaces = self.controller.list(
            filters={
                'resource_types': [RESOURCE_TYPE1]
            }
        )

        self.assertEqual(1, len(namespaces))
        self.assertEqual(NAMESPACE3, namespaces[0]['namespace'])

    def test_list_namespaces_with_multiple_resource_types_filter(self):
        namespaces = self.controller.list(
            filters={
                'resource_types': [RESOURCE_TYPE1, RESOURCE_TYPE2]
            }
        )

        self.assertEqual(1, len(namespaces))
        self.assertEqual(NAMESPACE4, namespaces[0]['namespace'])

    def test_list_namespaces_with_visibility_filter(self):
        namespaces = self.controller.list(
            filters={
                'visibility': 'private'
            }
        )

        self.assertEqual(1, len(namespaces))
        self.assertEqual(NAMESPACE5, namespaces[0]['namespace'])

    def test_get_namespace(self):
        namespace = self.controller.get(NAMESPACE1)
        self.assertEqual(NAMESPACE1, namespace.namespace)
        self.assertTrue(namespace.protected)

    def test_get_namespace_with_resource_type(self):
        namespace = self.controller.get(NAMESPACE6,
                                        resource_type=RESOURCE_TYPE1)
        self.assertEqual(NAMESPACE6, namespace.namespace)
        self.assertTrue(namespace.protected)

    def test_create_namespace(self):
        properties = {
            'namespace': NAMESPACENEW
        }
        namespace = self.controller.create(**properties)

        self.assertEqual(NAMESPACENEW, namespace.namespace)
        self.assertTrue(namespace.protected)

    def test_create_namespace_invalid_data(self):
        properties = {}

        self.assertRaises(TypeError, self.controller.create, **properties)

    def test_create_namespace_invalid_property(self):
        properties = {'namespace': 'NewNamespace', 'protected': '123'}

        self.assertRaises(TypeError, self.controller.create, **properties)

    def test_update_namespace(self):
        properties = {'display_name': 'My Updated Name'}
        namespace = self.controller.update(NAMESPACE1, **properties)

        self.assertEqual(NAMESPACE1, namespace.namespace)

    def test_update_namespace_invalid_property(self):
        properties = {'protected': '123'}

        self.assertRaises(TypeError, self.controller.update, NAMESPACE1,
                          **properties)

    def test_update_namespace_disallowed_fields(self):
        properties = {'display_name': 'My Updated Name'}
        self.controller.update(NAMESPACE1, **properties)
        actual = self.api.calls
        _disallowed_fields = ['self', 'schema', 'created_at', 'updated_at']
        for key in actual[1][3]:
            self.assertNotIn(key, _disallowed_fields)

    def test_delete_namespace(self):
        self.controller.delete(NAMESPACE1)
        expect = [
            ('DELETE',
             '/v2/metadefs/namespaces/%s' % NAMESPACE1,
             {},
             None)]
        self.assertEqual(expect, self.api.calls)
