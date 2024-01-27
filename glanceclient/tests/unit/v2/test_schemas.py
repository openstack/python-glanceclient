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

import jsonpatch
import testtools
import warlock

from glanceclient.tests import utils
from glanceclient.v2 import schemas


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
                    'name': {'type': 'string',
                             'description': 'Name of image'},
                    'tags': {'type': 'array'}
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
        'shape': {'type': 'string', 'is_base': False},
        'tags': {'type': 'array'}
    },
})


def compare_json_patches(a, b):
    """Return 0 if a and b describe the same JSON patch."""
    return (jsonpatch.JsonPatch.from_string(a) ==
            jsonpatch.JsonPatch.from_string(b))


class TestSchemaProperty(testtools.TestCase):
    def test_property_minimum(self):
        prop = schemas.SchemaProperty('size')
        self.assertEqual('size', prop.name)

    def test_property_description(self):
        prop = schemas.SchemaProperty('size', description='some quantity')
        self.assertEqual('size', prop.name)
        self.assertEqual('some quantity', prop.description)

    def test_property_is_base(self):
        prop1 = schemas.SchemaProperty('name')
        prop2 = schemas.SchemaProperty('foo', is_base=False)
        prop3 = schemas.SchemaProperty('foo', is_base=True)
        self.assertTrue(prop1.is_base)
        self.assertFalse(prop2.is_base)
        self.assertTrue(prop3.is_base)


class TestSchema(testtools.TestCase):
    def test_schema_minimum(self):
        raw_schema = {'name': 'Country', 'properties': {}}
        schema = schemas.Schema(raw_schema)
        self.assertEqual('Country', schema.name)
        self.assertEqual([], schema.properties)

    def test_schema_with_property(self):
        raw_schema = {'name': 'Country', 'properties': {'size': {}}}
        schema = schemas.Schema(raw_schema)
        self.assertEqual('Country', schema.name)
        self.assertEqual(['size'], [p.name for p in schema.properties])

    def test_raw(self):
        raw_schema = {'name': 'Country', 'properties': {}}
        schema = schemas.Schema(raw_schema)
        self.assertEqual(raw_schema, schema.raw())

    def test_property_is_base(self):
        raw_schema = {'name': 'Country',
                      'properties': {
                          'size': {},
                          'population': {'is_base': False}}}
        schema = schemas.Schema(raw_schema)
        self.assertTrue(schema.is_base_property('size'))
        self.assertFalse(schema.is_base_property('population'))
        self.assertFalse(schema.is_base_property('foo'))


class TestController(testtools.TestCase):
    def setUp(self):
        super(TestController, self).setUp()
        self.api = utils.FakeAPI(fixtures)
        self.controller = schemas.Controller(self.api)

    def test_get_schema(self):
        schema = self.controller.get('image')
        self.assertEqual('image', schema.name)
        self.assertEqual(set(['name', 'tags']),
                         set([p.name for p in schema.properties]))


class TestSchemaBasedModel(testtools.TestCase):
    def setUp(self):
        super(TestSchemaBasedModel, self).setUp()
        self.model = warlock.model_factory(_SCHEMA.raw(),
                                           base_class=schemas.SchemaBasedModel)

    def test_patch_should_replace_missing_core_properties(self):
        obj = {
            'name': 'fred'
        }

        original = self.model(obj)
        original['color'] = 'red'

        patch = original.patch
        expected = '[{"path": "/color", "value": "red", "op": "replace"}]'
        self.assertTrue(compare_json_patches(patch, expected))

    def test_patch_should_add_extra_properties(self):
        obj = {
            'name': 'fred',
        }

        original = self.model(obj)
        original['weight'] = '10'

        patch = original.patch
        expected = '[{"path": "/weight", "value": "10", "op": "add"}]'
        self.assertTrue(compare_json_patches(patch, expected))

    def test_patch_should_replace_extra_properties(self):
        obj = {
            'name': 'fred',
            'weight': '10'
        }

        original = self.model(obj)
        original['weight'] = '22'

        patch = original.patch
        expected = '[{"path": "/weight", "value": "22", "op": "replace"}]'
        self.assertTrue(compare_json_patches(patch, expected))

    def test_patch_should_remove_extra_properties(self):
        obj = {
            'name': 'fred',
            'weight': '10'
        }

        original = self.model(obj)
        del original['weight']

        patch = original.patch
        expected = '[{"path": "/weight", "op": "remove"}]'
        self.assertTrue(compare_json_patches(patch, expected))

    def test_patch_should_remove_core_properties(self):
        obj = {
            'name': 'fred',
            'color': 'red'
        }

        original = self.model(obj)
        del original['color']

        patch = original.patch
        expected = '[{"path": "/color", "op": "remove"}]'
        self.assertTrue(compare_json_patches(patch, expected))

    def test_patch_should_add_missing_custom_properties(self):
        obj = {
            'name': 'fred'
        }

        original = self.model(obj)
        original['shape'] = 'circle'

        patch = original.patch
        expected = '[{"path": "/shape", "value": "circle", "op": "add"}]'
        self.assertTrue(compare_json_patches(patch, expected))

    def test_patch_should_replace_custom_properties(self):
        obj = {
            'name': 'fred',
            'shape': 'circle'
        }

        original = self.model(obj)
        original['shape'] = 'square'

        patch = original.patch
        expected = '[{"path": "/shape", "value": "square", "op": "replace"}]'
        self.assertTrue(compare_json_patches(patch, expected))

    def test_patch_should_replace_tags(self):
        obj = {'name': 'fred', }

        original = self.model(obj)
        original['tags'] = ['tag1', 'tag2']

        patch = original.patch
        expected = '[{"path": "/tags", "value": ["tag1", "tag2"], ' \
            '"op": "replace"}]'
        self.assertTrue(compare_json_patches(patch, expected))
