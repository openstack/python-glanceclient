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
        raise NotImplementedError()

    def update(self, artifact_id, type_name=None, type_version=None,
               remove_props=None, **kwargs):
        raise NotImplementedError()

    def get(self, artifact_id, type_name=None, type_version=None,
            show_level=None):
        raise NotImplementedError()

    def list(self, type_name=None, type_version=None, **kwargs):
        raise NotImplementedError()

    def active(self, artifact_id, type_name=None, type_version=None):
        raise NotImplementedError()

    def deactivate(self, artifact_id, type_name=None, type_version=None):
        raise NotImplementedError()

    def delete(self, artifact_id, type_name=None, type_version=None):
        raise NotImplementedError()

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
