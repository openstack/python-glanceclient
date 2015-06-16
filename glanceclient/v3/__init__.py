# Copyright (c) 2015 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import six

from glanceclient import exc


class ArtifactType(object):
    generic_properties = ('created_at', 'id', 'name', 'owner', 'state',
                          'type_name', 'type_version', 'updated_at',
                          'version', 'visibility', 'description', 'tags',
                          'published_at', 'deleted_at')

    supported_show_levels = ('none', 'basic', 'direct', 'transitive')

    def __init__(self, **kwargs):
        try:
            for prop in self.generic_properties:
                setattr(self, prop, kwargs.pop(prop))
        except KeyError:
            msg = "Invalid parameters were provided"
            raise exc.HTTPBadRequest(msg)
        self.type_specific_properties = {}
        for key, value in six.iteritems(kwargs):
            try:
                if _is_dependency(value):

                    self.type_specific_properties[key] = ArtifactType(**value)
                elif _is_dependencies_list(value):

                    self.type_specific_properties[key] = [ArtifactType(**elem)
                                                          for elem in value]
                else:
                    self.type_specific_properties[key] = value
            except exc.HTTPBadRequest:
                # if it's not possible to generate artifact object then
                # assign the value as a regular dict.
                self.type_specific_properties[key] = value


def _is_dependency(d):
    if type(d) is dict and d.get('type_name') and d.get('type_version'):
        return True
    return False


def _is_dependencies_list(l):
    if type(l) is list and all(_is_dependency(d) for d in l):
        return True
    return False
