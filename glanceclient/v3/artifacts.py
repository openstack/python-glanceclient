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

from glanceclient import exc
from glanceclient.v3 import ArtifactType


class Controller(object):
    def __init__(self, http_client, type_name=None, type_version=None):
        self.http_client = http_client
        self.type_name = type_name
        self.type_version = type_version

    def _check_type_params(self, type_name, type_version):
        """Check that type name and type versions were specified"""
        type_name = type_name or self.type_name
        type_version = type_version or self.type_version

        if type_name is None:
            msg = "Type name must be specified"
            raise exc.HTTPBadRequest(msg)

        if type_version is None:
            msg = "Type version must be specified"
            raise exc.HTTPBadRequest(msg)

        return type_name, type_version

    def create(self, name, version, type_name=None, type_version=None,
               **kwargs):
        """Create an artifact of given type and version.

        :param name: name of creating artifact.
        :param version: semver string describing an artifact version
        """
        type_name, type_version = self._check_type_params(type_name,
                                                          type_version)
        kwargs.update({'name': name, 'version': version})
        url = '/v3/artifacts/%s/v%s/drafts' % (type_name, type_version)
        resp, body = self.http_client.post(url, data=kwargs)
        return ArtifactType(**body)

    def update(self, artifact_id, type_name=None, type_version=None,
               remove_props=None, **kwargs):
        """Update attributes of an artifact.

        :param artifact_id: ID of the artifact to modify.
        :param remove_props: List of property names to remove
        :param \*\*kwargs: Artifact attribute names and their new values.
        """
        type_name, type_version = self._check_type_params(type_name,
                                                          type_version)
        url = '/v3/artifacts/%s/v%s/%s' % (type_name, type_version,
                                           artifact_id)
        hdrs = {
            'Content-Type': 'application/openstack-images-v2.1-json-patch'}

        artifact_obj = self.get(artifact_id, type_name, type_version)

        changes = []
        if remove_props:
            for prop in remove_props:
                if prop in ArtifactType.generic_properties:
                    msg = "Generic properties cannot be removed"
                    raise exc.HTTPBadRequest(msg)
                if prop not in kwargs:
                    changes.append({'op': 'remove',
                                    'path': '/' + prop})

        for prop in kwargs:
            if prop in artifact_obj.generic_properties:
                op = 'add' if getattr(artifact_obj,
                                      prop) is None else 'replace'
            elif prop in artifact_obj.type_specific_properties:
                if artifact_obj.type_specific_properties[prop] is None:
                    op = 'add'
                else:
                    op = 'replace'
            else:
                msg = ("Property '%s' doesn't exist in type '%s' with version"
                       " '%s'" % (prop, type_name, type_version))
                raise exc.HTTPBadRequest(msg)
            changes.append({'op': op, 'path': '/' + prop,
                            'value': kwargs[prop]})

        resp, body = self.http_client.patch(url, headers=hdrs, data=changes)
        return ArtifactType(**body)

    def get(self, artifact_id, type_name=None, type_version=None,
            show_level=None):
        """Get information about an artifact.

        :param artifact_id: ID of the artifact to get.
        :param show_level: value of datalization. Possible values:
                           "none", "basic", "direct", "transitive"
        """
        type_name, type_version = self._check_type_params(type_name,
                                                          type_version)

        url = '/v3/artifacts/%s/v%s/%s' % (type_name, type_version,
                                           artifact_id)
        if show_level:
            if show_level not in ArtifactType.supported_show_levels:
                msg = "Invalid show level: %s" % show_level
                raise exc.HTTPBadRequest(msg)
            url += '?show_level=%s' % show_level
        resp, body = self.http_client.get(url)
        return ArtifactType(**body)

    def list(self, type_name=None, type_version=None, **kwargs):
        raise NotImplementedError()

    def active(self, artifact_id, type_name=None, type_version=None):
        raise NotImplementedError()

    def deactivate(self, artifact_id, type_name=None, type_version=None):
        raise NotImplementedError()

    def delete(self, artifact_id, type_name=None, type_version=None):
        """Delete an artifact and all its data.

        :param artifact_id: ID of the artifact to delete.
        """
        type_name, type_version = self._check_type_params(type_name,
                                                          type_version)
        url = '/v3/artifacts/%s/v%s/%s' % (type_name, type_version,
                                           artifact_id)
        self.http_client.delete(url)

    def upload_blob(self, artifact_id, blob_property, data, position=None,
                    type_name=None, type_version=None):
        raise NotImplementedError()

    def download_blob(self, artifact_id, blob_property, position=None,
                      type_name=None, type_version=None, do_checksum=True):
        raise NotImplementedError()

    def delete_blob(self, artifact_id, blob_property, position=None,
                    type_name=None, type_version=None):
        raise NotImplementedError()

    def add_property(self, artifact_id, dependency_id, position=None,
                     type_name=None, type_version=None):
        raise NotImplementedError()

    def replace_property(self, artifact_id, dependency_id, position=None,
                         type_name=None, type_version=None):
        raise NotImplementedError()

    def remove_property(self, artifact_id, dependency_id, position=None,
                        type_name=None, type_version=None):
        raise NotImplementedError()

    def artifact_export(self, artifact_id,
                        type_name=None, type_version=None):
        raise NotImplementedError()

    def artifact_import(self, data, type_name=None, type_version=None):
        raise NotImplementedError()
