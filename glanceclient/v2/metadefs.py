# Copyright 2014 OpenStack Foundation
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

import six
from six.moves.urllib import parse
import warlock

from glanceclient.common import utils
from glanceclient.openstack.common import strutils
from glanceclient.v2 import schemas

DEFAULT_PAGE_SIZE = 20


class NamespaceController(object):
    def __init__(self, http_client, schema_client):
        self.http_client = http_client
        self.schema_client = schema_client

    @utils.memoized_property
    def model(self):
        schema = self.schema_client.get('metadefs/namespace')
        return warlock.model_factory(schema.raw(), schemas.SchemaBasedModel)

    def create(self, **kwargs):
        """Create a namespace.

        :param kwargs: Unpacked namespace object.
        """
        url = '/v2/metadefs/namespaces'
        try:
            namespace = self.model(kwargs)
        except (warlock.InvalidOperation, ValueError) as e:
            raise TypeError(utils.exception_to_str(e))

        resp, body = self.http_client.post(url, data=namespace)
        body.pop('self', None)
        return self.model(**body)

    def update(self, namespace_name, **kwargs):
        """Update a namespace.

        :param namespace_name: Name of a namespace (old one).
        :param kwargs: Unpacked namespace object.
        """
        namespace = self.get(namespace_name)
        for (key, value) in six.iteritems(kwargs):
            try:
                setattr(namespace, key, value)
            except warlock.InvalidOperation as e:
                raise TypeError(utils.exception_to_str(e))

        # Remove read-only parameters.
        read_only = ['schema', 'updated_at', 'created_at']
        for elem in read_only:
            if elem in namespace:
                del namespace[elem]

        url = '/v2/metadefs/namespaces/{0}'.format(namespace_name)
        self.http_client.put(url, data=namespace)

        return self.get(namespace.namespace)

    def get(self, namespace, **kwargs):
        """Get one namespace."""
        query_params = parse.urlencode(kwargs)
        if kwargs:
            query_params = '?%s' % query_params

        url = '/v2/metadefs/namespaces/{0}{1}'.format(namespace, query_params)
        resp, body = self.http_client.get(url)
        # NOTE(bcwaldon): remove 'self' for now until we have an elegant
        # way to pass it into the model constructor without conflict
        body.pop('self', None)
        return self.model(**body)

    def list(self, **kwargs):
        """Retrieve a listing of Namespace objects

        :param page_size: Number of namespaces to request in each request
        :returns generator over list of Namespaces
        """

        ori_validate_fun = self.model.validate
        empty_fun = lambda *args, **kwargs: None

        def paginate(url):
            resp, body = self.http_client.get(url)
            for namespace in body['namespaces']:
                # NOTE(bcwaldon): remove 'self' for now until we have
                # an elegant way to pass it into the model constructor
                # without conflict.
                namespace.pop('self', None)
                yield self.model(**namespace)
                # NOTE(zhiyan): In order to resolve the performance issue
                # of JSON schema validation for image listing case, we
                # don't validate each image entry but do it only on first
                # image entry for each page.
                self.model.validate = empty_fun

            # NOTE(zhiyan); Reset validation function.
            self.model.validate = ori_validate_fun

            try:
                next_url = body['next']
            except KeyError:
                return
            else:
                for namespace in paginate(next_url):
                    yield namespace

        filters = kwargs.get('filters', {})
        filters = {} if filters is None else filters

        if not kwargs.get('page_size'):
            filters['limit'] = DEFAULT_PAGE_SIZE
        else:
            filters['limit'] = kwargs['page_size']

        for param, value in six.iteritems(filters):
            if isinstance(value, list):
                filters[param] = strutils.safe_encode(','.join(value))
            elif isinstance(value, six.string_types):
                filters[param] = strutils.safe_encode(value)

        url = '/v2/metadefs/namespaces?%s' % parse.urlencode(filters)

        for namespace in paginate(url):
            yield namespace

    def delete(self, namespace):
        """Delete a namespace."""
        url = '/v2/metadefs/namespaces/{0}'.format(namespace)
        self.http_client.delete(url)


class ResourceTypeController(object):
    def __init__(self, http_client, schema_client):
        self.http_client = http_client
        self.schema_client = schema_client

    @utils.memoized_property
    def model(self):
        schema = self.schema_client.get('metadefs/resource_type')
        return warlock.model_factory(schema.raw(), schemas.SchemaBasedModel)

    def associate(self, namespace, **kwargs):
        """Associate a resource type with a namespace."""
        try:
            res_type = self.model(kwargs)
        except (warlock.InvalidOperation, ValueError) as e:
            raise TypeError(utils.exception_to_str(e))

        url = '/v2/metadefs/namespaces/{0}/resource_types'.format(namespace,
                                                                  res_type)
        resp, body = self.http_client.post(url, data=res_type)
        body.pop('self', None)
        return self.model(**body)

    def deassociate(self, namespace, resource):
        """Deasociate a resource type with a namespace."""
        url = '/v2/metadefs/namespaces/{0}/resource_types/{1}'. \
            format(namespace, resource)
        self.http_client.delete(url)

    def list(self):
        """Retrieve a listing of available resource types

        :returns generator over list of resource_types
        """

        url = '/v2/metadefs/resource_types'
        resp, body = self.http_client.get(url)
        for resource_type in body['resource_types']:
            yield self.model(**resource_type)

    def get(self, namespace):
        url = '/v2/metadefs/namespaces/{0}/resource_types'.format(namespace)
        resp, body = self.http_client.get(url)
        body.pop('self', None)
        for resource_type in body['resource_type_associations']:
            yield self.model(**resource_type)


class PropertyController(object):
    def __init__(self, http_client, schema_client):
        self.http_client = http_client
        self.schema_client = schema_client

    @utils.memoized_property
    def model(self):
        schema = self.schema_client.get('metadefs/property')
        return warlock.model_factory(schema.raw(), schemas.SchemaBasedModel)

    def create(self, namespace, **kwargs):
        """Create a property.

        :param namespace: Name of a namespace the property will belong.
        :param kwargs: Unpacked property object.
        """
        try:
            prop = self.model(kwargs)
        except (warlock.InvalidOperation, ValueError) as e:
            raise TypeError(utils.exception_to_str(e))

        url = '/v2/metadefs/namespaces/{0}/properties'.format(namespace)

        resp, body = self.http_client.post(url, data=prop)
        body.pop('self', None)
        return self.model(**body)

    def update(self, namespace, prop_name, **kwargs):
        """Update a property.

        :param namespace: Name of a namespace the property belongs.
        :param prop_name: Name of a property (old one).
        :param kwargs: Unpacked property object.
        """
        prop = self.get(namespace, prop_name)
        for (key, value) in kwargs.items():
            try:
                setattr(prop, key, value)
            except warlock.InvalidOperation as e:
                raise TypeError(utils.exception_to_str(e))

        url = '/v2/metadefs/namespaces/{0}/properties/{1}'.format(namespace,
                                                                  prop_name)
        self.http_client.put(url, data=prop)

        return self.get(namespace, prop.name)

    def get(self, namespace, prop_name):
        url = '/v2/metadefs/namespaces/{0}/properties/{1}'.format(namespace,
                                                                  prop_name)
        resp, body = self.http_client.get(url)
        body.pop('self', None)
        body['name'] = prop_name
        return self.model(**body)

    def list(self, namespace, **kwargs):
        """Retrieve a listing of metadata properties

        :returns generator over list of objects
        """
        url = '/v2/metadefs/namespaces/{0}/properties'.format(namespace)

        resp, body = self.http_client.get(url)

        for key, value in body['properties'].items():
            value['name'] = key
            yield self.model(value)

    def delete(self, namespace, prop_name):
        """Delete a property."""
        url = '/v2/metadefs/namespaces/{0}/properties/{1}'.format(namespace,
                                                                  prop_name)
        self.http_client.delete(url)

    def delete_all(self, namespace):
        """Delete all properties in a namespace."""
        url = '/v2/metadefs/namespaces/{0}/properties'.format(namespace)
        self.http_client.delete(url)


class ObjectController(object):
    def __init__(self, http_client, schema_client):
        self.http_client = http_client
        self.schema_client = schema_client

    @utils.memoized_property
    def model(self):
        schema = self.schema_client.get('metadefs/object')
        return warlock.model_factory(schema.raw(), schemas.SchemaBasedModel)

    def create(self, namespace, **kwargs):
        """Create an object.

        :param namespace: Name of a namespace the object belongs.
        :param kwargs: Unpacked object.
        """
        try:
            obj = self.model(kwargs)
        except (warlock.InvalidOperation, ValueError) as e:
            raise TypeError(utils.exception_to_str(e))

        url = '/v2/metadefs/namespaces/{0}/objects'.format(namespace)

        resp, body = self.http_client.post(url, data=obj)
        body.pop('self', None)
        return self.model(**body)

    def update(self, namespace, object_name, **kwargs):
        """Update an object.

        :param namespace: Name of a namespace the object belongs.
        :param prop_name: Name of an object (old one).
        :param kwargs: Unpacked object.
        """
        obj = self.get(namespace, object_name)
        for (key, value) in kwargs.items():
            try:
                setattr(obj, key, value)
            except warlock.InvalidOperation as e:
                raise TypeError(utils.exception_to_str(e))

        # Remove read-only parameters.
        read_only = ['schema', 'updated_at', 'created_at']
        for elem in read_only:
            if elem in namespace:
                del namespace[elem]

        url = '/v2/metadefs/namespaces/{0}/objects/{1}'.format(namespace,
                                                               object_name)
        self.http_client.put(url, data=obj)

        return self.get(namespace, obj.name)

    def get(self, namespace, object_name):
        url = '/v2/metadefs/namespaces/{0}/objects/{1}'.format(namespace,
                                                               object_name)
        resp, body = self.http_client.get(url)
        body.pop('self', None)
        return self.model(**body)

    def list(self, namespace, **kwargs):
        """Retrieve a listing of metadata objects

        :returns generator over list of objects
        """
        url = '/v2/metadefs/namespaces/{0}/objects'.format(namespace,)
        resp, body = self.http_client.get(url)

        for obj in body['objects']:
            yield self.model(obj)

    def delete(self, namespace, object_name):
        """Delete an object."""
        url = '/v2/metadefs/namespaces/{0}/objects/{1}'.format(namespace,
                                                               object_name)
        self.http_client.delete(url)

    def delete_all(self, namespace):
        """Delete all objects in a namespace."""
        url = '/v2/metadefs/namespaces/{0}/objects'.format(namespace)
        self.http_client.delete(url)
