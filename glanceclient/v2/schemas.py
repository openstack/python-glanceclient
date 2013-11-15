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

import copy
import jsonpatch
import warlock.model as warlock


class SchemaBasedModel(warlock.Model):
    """Glance specific subclass of the warlock Model

    This implementation alters the function of the patch property
    to take into account the schema's core properties. With this version
    undefined properties which are core will generated 'replace'
    operations rather than 'add' since this is what the Glance API
    expects.
    """

    @warlock.Model.patch.getter
    def patch(self):
        """Return a jsonpatch object representing the delta."""
        original = copy.deepcopy(self.__dict__['__original__'])
        new = dict(self)
        if self.__dict__['schema']:
            for prop in self.schema['properties']:
                if prop not in original and prop in new:
                    original[prop] = None

        return jsonpatch.make_patch(original, dict(self)).to_string()


class SchemaProperty(object):
    def __init__(self, name, **kwargs):
        self.name = name
        self.description = kwargs.get('description')


def translate_schema_properties(schema_properties):
    """Parse the properties dictionary of a schema document

    :returns list of SchemaProperty objects
    """
    properties = []
    for (name, prop) in schema_properties.items():
        properties.append(SchemaProperty(name, **prop))
    return properties


class Schema(object):
    def __init__(self, raw_schema):
        self._raw_schema = raw_schema
        self.name = raw_schema['name']
        raw_properties = raw_schema['properties']
        self.properties = translate_schema_properties(raw_properties)

    def is_core_property(self, property_name):
        for prop in self.properties:
            if property_name == prop.name:
                return True
        return False

    def raw(self):
        return copy.deepcopy(self._raw_schema)


class Controller(object):
    def __init__(self, http_client):
        self.http_client = http_client

    def get(self, schema_name):
        uri = '/v2/schemas/%s' % schema_name
        _, raw_schema = self.http_client.json_request('GET', uri)
        return Schema(raw_schema)
