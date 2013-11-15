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
import warlock

from glanceclient.v2 import schemas
from tests import utils


fixtures = {
    '/v2/schemas': {
        'GET': (
            {},
            {
                'image': '/v2/schemas/image',
                'access': '/v2/schemas/image/access',
            },
        ),
    },
    '/v2/schemas/image': {
        'GET': (
            {},
            {
                'name': 'image',
                'properties': {
                    'name': {'type': 'string', 'description': 'Name of image'},
                },
            },
        ),
    },
}


_SCHEMA = schemas.Schema({
    'name': 'image',
    'properties': {
        'name': {'type': 'string'},
        'color': {'type': 'string'},
    },
})


class TestSchemaProperty(testtools.TestCase):
    def test_property_minimum(self):
        prop = schemas.SchemaProperty('size')
        self.assertEqual(prop.name, 'size')

    def test_property_description(self):
        prop = schemas.SchemaProperty('size', description='some quantity')
        self.assertEqual(prop.name, 'size')
        self.assertEqual(prop.description, 'some quantity')


class TestSchema(testtools.TestCase):
    def test_schema_minimum(self):
        raw_schema = {'name': 'Country', 'properties': {}}
        schema = schemas.Schema(raw_schema)
        self.assertEqual(schema.name, 'Country')
        self.assertEqual(schema.properties, [])

    def test_schema_with_property(self):
        raw_schema = {'name': 'Country', 'properties': {'size': {}}}
        schema = schemas.Schema(raw_schema)
        self.assertEqual(schema.name, 'Country')
        self.assertEqual([p.name for p in schema.properties], ['size'])

    def test_raw(self):
        raw_schema = {'name': 'Country', 'properties': {}}
        schema = schemas.Schema(raw_schema)
        self.assertEqual(schema.raw(), raw_schema)


class TestController(testtools.TestCase):
    def setUp(self):
        super(TestController, self).setUp()
        self.api = utils.FakeAPI(fixtures)
        self.controller = schemas.Controller(self.api)

    def test_get_schema(self):
        schema = self.controller.get('image')
        self.assertEqual(schema.name, 'image')
        self.assertEqual([p.name for p in schema.properties], ['name'])


class TestSchemaBasedModel(testtools.TestCase):
    def setUp(self):
        super(TestSchemaBasedModel, self).setUp()
        self.model = warlock.model_factory(_SCHEMA.raw(),
                                           schemas.SchemaBasedModel)

    def test_patch_should_replace_missing_core_properties(self):
        obj = {
            'name': 'fred'
        }

        original = self.model(obj)
        original['color'] = 'red'

        patch = original.patch
        expected = '[{"path": "/color", "value": "red", "op": "replace"}]'
        self.assertEqual(patch, expected)

    def test_patch_should_add_extra_properties(self):
        obj = {
            'name': 'fred',
        }

        original = self.model(obj)
        original['weight'] = '10'

        patch = original.patch
        expected = '[{"path": "/weight", "value": "10", "op": "add"}]'
        self.assertEqual(patch, expected)

    def test_patch_should_replace_extra_properties(self):
        obj = {
            'name': 'fred',
            'weight': '10'
        }

        original = self.model(obj)
        original['weight'] = '22'

        patch = original.patch
        expected = '[{"path": "/weight", "value": "22", "op": "replace"}]'
        self.assertEqual(patch, expected)

    def test_patch_should_remove_extra_properties(self):
        obj = {
            'name': 'fred',
            'weight': '10'
        }

        original = self.model(obj)
        del original['weight']

        patch = original.patch
        expected = '[{"path": "/weight", "op": "remove"}]'
        self.assertEqual(patch, expected)

    def test_patch_should_remove_core_properties(self):
        obj = {
            'name': 'fred',
            'color': 'red'
        }

        original = self.model(obj)
        del original['color']

        patch = original.patch
        expected = '[{"path": "/color", "op": "remove"}]'
        self.assertEqual(patch, expected)
