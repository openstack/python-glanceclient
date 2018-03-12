# Copyright 2016 NTT DATA
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import testtools


class BaseController(testtools.TestCase):
    def __init__(self, api, schema_api, controller_class):
        self.controller = controller_class(api, schema_api)

    def _assertRequestId(self, obj):
        self.assertIsNotNone(getattr(obj, 'request_ids', None))
        self.assertEqual(['req-1234'], obj.request_ids)

    def list(self, *args, **kwargs):
        gen_obj = self.controller.list(*args, **kwargs)
        # For generator cases the request_ids property will be an empty list
        # until the underlying generator is invoked at-least once.
        resources = list(gen_obj)
        if len(resources) > 0:
            self._assertRequestId(gen_obj)
        else:
            # If list is empty that means geneator object has raised
            # StopIteration for first iteration and will not contain the
            # request_id in it.
            self.assertEqual([], gen_obj.request_ids)

        return resources

    def get(self, *args, **kwargs):
        resource = self.controller.get(*args, **kwargs)

        self._assertRequestId(resource)
        return resource

    def create(self, *args, **kwargs):
        resource = self.controller.create(*args, **kwargs)
        self._assertRequestId(resource)
        return resource

    def create_multiple(self, *args, **kwargs):
        tags = self.controller.create_multiple(*args, **kwargs)
        actual = [tag.name for tag in tags]
        self._assertRequestId(tags)
        return actual

    def update(self, *args, **properties):
        resource = self.controller.update(*args, **properties)
        self._assertRequestId(resource)
        return resource

    def delete(self, *args):
        resp = self.controller.delete(*args)
        self._assertRequestId(resp)

    def delete_all(self, *args):
        resp = self.controller.delete_all(*args)
        self._assertRequestId(resp)

    def deactivate(self, *args):
        resp = self.controller.deactivate(*args)
        self._assertRequestId(resp)

    def reactivate(self, *args):
        resp = self.controller.reactivate(*args)
        self._assertRequestId(resp)

    def upload(self, *args, **kwargs):
        resp = self.controller.upload(*args, **kwargs)
        self._assertRequestId(resp)

    def data(self, *args, **kwargs):
        body = self.controller.data(*args, **kwargs)
        self._assertRequestId(body)
        return body

    def delete_locations(self, *args):
        resp = self.controller.delete_locations(*args)
        self._assertRequestId(resp)

    def add_location(self, *args, **kwargs):
        resp = self.controller.add_location(*args, **kwargs)
        self._assertRequestId(resp)

    def update_location(self, *args, **kwargs):
        resp = self.controller.update_location(*args, **kwargs)
        self._assertRequestId(resp)

    def associate(self, *args, **kwargs):
        resource_types = self.controller.associate(*args, **kwargs)
        self._assertRequestId(resource_types)
        return resource_types

    def deassociate(self, *args):
        resp = self.controller.deassociate(*args)
        self._assertRequestId(resp)

    def image_import(self, *args):
        resp = self.controller.image_import(*args)
        self._assertRequestId(resp)


class BaseResourceTypeController(BaseController):
    def __init__(self, api, schema_api, controller_class):
        super(BaseResourceTypeController, self).__init__(api, schema_api,
                                                         controller_class)

    def get(self, *args, **kwargs):
        resource_types = self.controller.get(*args)
        names = [rt.name for rt in resource_types]
        self._assertRequestId(resource_types)
        return names
