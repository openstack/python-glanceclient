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

from oslo_utils import encodeutils
import urllib.parse
import warlock

from glanceclient.common import utils
from glanceclient.v2 import schemas

DEFAULT_PAGE_SIZE = 20
SORT_DIR_VALUES = ('asc', 'desc')
SORT_KEY_VALUES = ('created_at', 'namespace')


class NamespaceController(object):
    def __init__(self, http_client, schema_client):
        self.http_client = http_client
        self.schema_client = schema_client

    @utils.memoized_property
    def model(self):
        schema = self.schema_client.get('metadefs/namespace')
        return warlock.model_factory(schema.raw(),
                                     base_class=schemas.SchemaBasedModel)

    @utils.add_req_id_to_object()
    def create(self, **kwargs):
        """Create a namespace.

        :param kwargs: Unpacked namespace object.
        """
        url = '/v2/metadefs/namespaces'
        try:
            namespace = self.model(kwargs)
        except (warlock.InvalidOperation, ValueError) as e:
            raise TypeError(str(e))

        resp, body = self.http_client.post(url, data=namespace)
        body.pop('self', None)
        return self.model(**body), resp

    def update(self, namespace_name, **kwargs):
        """Update a namespace.

        :param namespace_name: Name of a namespace (old one).
        :param kwargs: Unpacked namespace object.
        """
        namespace = self.get(namespace_name)
        for (key, value) in kwargs.items():
            try:
                setattr(namespace, key, value)
            except warlock.InvalidOperation as e:
                raise TypeError(str(e))

        # Remove read-only parameters.
        read_only = ['schema', 'updated_at', 'created_at']
        for elem in read_only:
            if elem in namespace:
                del namespace[elem]

        url = '/v2/metadefs/namespaces/%(namespace)s' % {
            'namespace': namespace_name}
        # Pass the original wrapped value to http client.
        resp, _ = self.http_client.put(url, data=namespace.wrapped)
        # Get request id from `put` request so it can be passed to the
        #  following `get` call
        req_id_hdr = {
            'x-openstack-request-id': utils._extract_request_id(resp)
        }
        return self._get(namespace.namespace, header=req_id_hdr)

    def get(self, namespace, **kwargs):
        return self._get(namespace, **kwargs)

    @utils.add_req_id_to_object()
    def _get(self, namespace, header=None, **kwargs):
        """Get one namespace."""
        query_params = urllib.parse.urlencode(kwargs)
        if kwargs:
            query_params = '?%s' % query_params

        url = '/v2/metadefs/namespaces/%(namespace)s%(query_params)s' % {
            'namespace': namespace, 'query_params': query_params}
        header = header or {}
        resp, body = self.http_client.get(url, headers=header)
        # NOTE(bcwaldon): remove 'self' for now until we have an elegant
        # way to pass it into the model constructor without conflict
        body.pop('self', None)
        return self.model(**body), resp

    @utils.add_req_id_to_generator()
    def list(self, **kwargs):
        """Retrieve a listing of Namespace objects.

        :param page_size: Number of items to request in each paginated request
        :param limit: Use to request a specific page size. Expect a response
                      to a limited request to return between zero and limit
                      items.
        :param marker: Specifies the namespace of the last-seen namespace.
                       The typical pattern of limit and marker is to make an
                       initial limited request and then to use the last
                       namespace from the response as the marker parameter
                       in a subsequent limited request.
        :param sort_key: The field to sort on (for example, 'created_at')
        :param sort_dir: The direction to sort ('asc' or 'desc')
        :returns: generator over list of Namespaces

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
                yield self.model(**namespace), resp
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
                for namespace, resp in paginate(next_url):
                    yield namespace, resp

        filters = kwargs.get('filters', {})
        filters = {} if filters is None else filters

        if not kwargs.get('page_size'):
            filters['limit'] = DEFAULT_PAGE_SIZE
        else:
            filters['limit'] = kwargs['page_size']

        if 'marker' in kwargs:
            filters['marker'] = kwargs['marker']

        sort_key = kwargs.get('sort_key')
        if sort_key is not None:
            if sort_key in SORT_KEY_VALUES:
                filters['sort_key'] = sort_key
            else:
                raise ValueError('sort_key must be one of the following: %s.'
                                 % ', '.join(SORT_KEY_VALUES))

        sort_dir = kwargs.get('sort_dir')
        if sort_dir is not None:
            if sort_dir in SORT_DIR_VALUES:
                filters['sort_dir'] = sort_dir
            else:
                raise ValueError('sort_dir must be one of the following: %s.'
                                 % ', '.join(SORT_DIR_VALUES))

        for param, value in filters.items():
            if isinstance(value, list):
                filters[param] = encodeutils.safe_encode(','.join(value))
            elif isinstance(value, str):
                filters[param] = encodeutils.safe_encode(value)

        url = '/v2/metadefs/namespaces?%s' % urllib.parse.urlencode(filters)

        for namespace, resp in paginate(url):
            yield namespace, resp

    @utils.add_req_id_to_object()
    def delete(self, namespace):
        """Delete a namespace."""
        url = '/v2/metadefs/namespaces/%(namespace)s' % {
            'namespace': namespace}
        resp, body = self.http_client.delete(url)
        return (resp, body), resp


class ResourceTypeController(object):
    def __init__(self, http_client, schema_client):
        self.http_client = http_client
        self.schema_client = schema_client

    @utils.memoized_property
    def model(self):
        schema = self.schema_client.get('metadefs/resource_type')
        return warlock.model_factory(schema.raw(),
                                     base_class=schemas.SchemaBasedModel)

    @utils.add_req_id_to_object()
    def associate(self, namespace, **kwargs):
        """Associate a resource type with a namespace."""
        try:
            res_type = self.model(kwargs)
        except (warlock.InvalidOperation, ValueError) as e:
            raise TypeError(str(e))

        url = '/v2/metadefs/namespaces/%(namespace)s/resource_types' % {
            'namespace': namespace}
        resp, body = self.http_client.post(url, data=res_type)
        body.pop('self', None)
        return self.model(**body), resp

    @utils.add_req_id_to_object()
    def deassociate(self, namespace, resource):
        """Deassociate a resource type with a namespace."""
        url = ('/v2/metadefs/namespaces/%(namespace)s/'
               'resource_types/%(resource)s') % {
            'namespace': namespace, 'resource': resource}
        resp, body = self.http_client.delete(url)
        return (resp, body), resp

    @utils.add_req_id_to_generator()
    def list(self):
        """Retrieve a listing of available resource types.

        :returns: generator over list of resource_types
        """

        url = '/v2/metadefs/resource_types'
        resp, body = self.http_client.get(url)
        for resource_type in body['resource_types']:
            yield self.model(**resource_type), resp

    @utils.add_req_id_to_generator()
    def get(self, namespace):
        url = '/v2/metadefs/namespaces/%(namespace)s/resource_types' % {
            'namespace': namespace}
        resp, body = self.http_client.get(url)
        body.pop('self', None)
        for resource_type in body['resource_type_associations']:
            yield self.model(**resource_type), resp


class PropertyController(object):
    def __init__(self, http_client, schema_client):
        self.http_client = http_client
        self.schema_client = schema_client

    @utils.memoized_property
    def model(self):
        schema = self.schema_client.get('metadefs/property')
        return warlock.model_factory(schema.raw(),
                                     base_class=schemas.SchemaBasedModel)

    @utils.add_req_id_to_object()
    def create(self, namespace, **kwargs):
        """Create a property.

        :param namespace: Name of a namespace the property will belong.
        :param kwargs: Unpacked property object.
        """
        try:
            prop = self.model(kwargs)
        except (warlock.InvalidOperation, ValueError) as e:
            raise TypeError(str(e))

        url = '/v2/metadefs/namespaces/%(namespace)s/properties' % {
            'namespace': namespace}
        resp, body = self.http_client.post(url, data=prop)
        body.pop('self', None)
        return self.model(**body), resp

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
                raise TypeError(str(e))

        url = ('/v2/metadefs/namespaces/%(namespace)s/'
               'properties/%(prop_name)s') % {
            'namespace': namespace, 'prop_name': prop_name}
        # Pass the original wrapped value to http client.
        resp, _ = self.http_client.put(url, data=prop.wrapped)
        # Get request id from `put` request so it can be passed to the
        #  following `get` call
        req_id_hdr = {
            'x-openstack-request-id': utils._extract_request_id(resp)}

        return self._get(namespace, prop.name, req_id_hdr)

    def get(self, namespace, prop_name):
        return self._get(namespace, prop_name)

    @utils.add_req_id_to_object()
    def _get(self, namespace, prop_name, header=None):
        url = ('/v2/metadefs/namespaces/%(namespace)s/'
               'properties/%(prop_name)s') % {
            'namespace': namespace, 'prop_name': prop_name}
        header = header or {}
        resp, body = self.http_client.get(url, headers=header)
        body.pop('self', None)
        body['name'] = prop_name
        return self.model(**body), resp

    @utils.add_req_id_to_generator()
    def list(self, namespace, **kwargs):
        """Retrieve a listing of metadata properties.

        :returns: generator over list of objects
        """
        url = '/v2/metadefs/namespaces/%(namespace)s/properties' % {
            'namespace': namespace}

        resp, body = self.http_client.get(url)

        for key, value in body['properties'].items():
            value['name'] = key
            yield self.model(value), resp

    @utils.add_req_id_to_object()
    def delete(self, namespace, prop_name):
        """Delete a property."""
        url = ('/v2/metadefs/namespaces/%(namespace)s/'
               'properties/%(prop_name)s') % {
            'namespace': namespace, 'prop_name': prop_name}
        resp, body = self.http_client.delete(url)
        return (resp, body), resp

    @utils.add_req_id_to_object()
    def delete_all(self, namespace):
        """Delete all properties in a namespace."""
        url = '/v2/metadefs/namespaces/%(namespace)s/properties' % {
            'namespace': namespace}
        resp, body = self.http_client.delete(url)
        return (resp, body), resp


class ObjectController(object):
    def __init__(self, http_client, schema_client):
        self.http_client = http_client
        self.schema_client = schema_client

    @utils.memoized_property
    def model(self):
        schema = self.schema_client.get('metadefs/object')
        return warlock.model_factory(schema.raw(),
                                     base_class=schemas.SchemaBasedModel)

    @utils.add_req_id_to_object()
    def create(self, namespace, **kwargs):
        """Create an object.

        :param namespace: Name of a namespace the object belongs.
        :param kwargs: Unpacked object.
        """
        try:
            obj = self.model(kwargs)
        except (warlock.InvalidOperation, ValueError) as e:
            raise TypeError(str(e))

        url = '/v2/metadefs/namespaces/%(namespace)s/objects' % {
            'namespace': namespace}

        resp, body = self.http_client.post(url, data=obj)
        body.pop('self', None)
        return self.model(**body), resp

    def update(self, namespace, object_name, **kwargs):
        """Update an object.

        :param namespace: Name of a namespace the object belongs.
        :param object_name: Name of an object (old one).
        :param kwargs: Unpacked object.
        """
        obj = self.get(namespace, object_name)
        for (key, value) in kwargs.items():
            try:
                setattr(obj, key, value)
            except warlock.InvalidOperation as e:
                raise TypeError(str(e))

        # Remove read-only parameters.
        read_only = ['schema', 'updated_at', 'created_at']
        for elem in read_only:
            if elem in obj:
                del obj[elem]

        url = ('/v2/metadefs/namespaces/%(namespace)s/'
               'objects/%(object_name)s') % {
            'namespace': namespace, 'object_name': object_name}
        # Pass the original wrapped value to http client.
        resp, _ = self.http_client.put(url, data=obj.wrapped)
        # Get request id from `put` request so it can be passed to the
        #  following `get` call
        req_id_hdr = {
            'x-openstack-request-id': utils._extract_request_id(resp)}

        return self._get(namespace, obj.name, req_id_hdr)

    def get(self, namespace, object_name):
        return self._get(namespace, object_name)

    @utils.add_req_id_to_object()
    def _get(self, namespace, object_name, header=None):
        url = ('/v2/metadefs/namespaces/%(namespace)s/'
               'objects/%(object_name)s') % {
            'namespace': namespace, 'object_name': object_name}
        header = header or {}
        resp, body = self.http_client.get(url, headers=header)
        body.pop('self', None)
        return self.model(**body), resp

    @utils.add_req_id_to_generator()
    def list(self, namespace, **kwargs):
        """Retrieve a listing of metadata objects.

        :returns: generator over list of objects
        """
        url = '/v2/metadefs/namespaces/%(namespace)s/objects' % {
            'namespace': namespace}
        resp, body = self.http_client.get(url)

        for obj in body['objects']:
            yield self.model(obj), resp

    @utils.add_req_id_to_object()
    def delete(self, namespace, object_name):
        """Delete an object."""
        url = ('/v2/metadefs/namespaces/%(namespace)s/'
               'objects/%(object_name)s') % {
            'namespace': namespace, 'object_name': object_name}
        resp, body = self.http_client.delete(url)
        return (resp, body), resp

    @utils.add_req_id_to_object()
    def delete_all(self, namespace):
        """Delete all objects in a namespace."""
        url = '/v2/metadefs/namespaces/%(namespace)s/objects' % {
            'namespace': namespace}
        resp, body = self.http_client.delete(url)
        return (resp, body), resp


class TagController(object):
    def __init__(self, http_client, schema_client):
        self.http_client = http_client
        self.schema_client = schema_client

    @utils.memoized_property
    def model(self):
        schema = self.schema_client.get('metadefs/tag')
        return warlock.model_factory(schema.raw(),
                                     base_class=schemas.SchemaBasedModel)

    @utils.add_req_id_to_object()
    def create(self, namespace, tag_name):
        """Create a tag.

        :param namespace: Name of a namespace the Tag belongs.
        :param tag_name: The name of the new tag to create.
        """

        url = '/v2/metadefs/namespaces/%(namespace)s/tags/%(tag_name)s' % {
            'namespace': namespace, 'tag_name': tag_name}

        resp, body = self.http_client.post(url)
        body.pop('self', None)
        return self.model(**body), resp

    @utils.add_req_id_to_generator()
    def create_multiple(self, namespace, **kwargs):
        """Create the list of tags.

        :param namespace: Name of a namespace to which the Tags belong.
        :param kwargs: list of tags, optional parameter append.
        """
        tag_names = kwargs.pop('tags', [])
        md_tag_list = []

        for tag_name in tag_names:
            try:
                md_tag_list.append(self.model(name=tag_name))
            except (warlock.InvalidOperation) as e:
                raise TypeError(str(e))
        tags = {'tags': md_tag_list}
        headers = {}

        url = '/v2/metadefs/namespaces/%(namespace)s/tags' % {
              'namespace': namespace}

        append = kwargs.pop('append', False)
        if append:
            headers['X-Openstack-Append'] = True
        resp, body = self.http_client.post(url, headers=headers, data=tags)
        body.pop('self', None)
        for tag in body['tags']:
            yield self.model(tag), resp

    def update(self, namespace, tag_name, **kwargs):
        """Update a tag.

        :param namespace: Name of a namespace the Tag belongs.
        :param tag_name: Name of the Tag (old one).
        :param kwargs: Unpacked tag.
        """
        tag = self.get(namespace, tag_name)
        for (key, value) in kwargs.items():
            try:
                setattr(tag, key, value)
            except warlock.InvalidOperation as e:
                raise TypeError(str(e))

        # Remove read-only parameters.
        read_only = ['updated_at', 'created_at']
        for elem in read_only:
            if elem in tag:
                del tag[elem]

        url = '/v2/metadefs/namespaces/%(namespace)s/tags/%(tag_name)s' % {
            'namespace': namespace, 'tag_name': tag_name}
        # Pass the original wrapped value to http client.
        resp, _ = self.http_client.put(url, data=tag.wrapped)
        # Get request id from `put` request so it can be passed to the
        #  following `get` call
        req_id_hdr = {
            'x-openstack-request-id': utils._extract_request_id(resp)}

        return self._get(namespace, tag.name, req_id_hdr)

    def get(self, namespace, tag_name):
        return self._get(namespace, tag_name)

    @utils.add_req_id_to_object()
    def _get(self, namespace, tag_name, header=None):
        url = '/v2/metadefs/namespaces/%(namespace)s/tags/%(tag_name)s' % {
            'namespace': namespace, 'tag_name': tag_name}
        header = header or {}
        resp, body = self.http_client.get(url, headers=header)
        body.pop('self', None)
        return self.model(**body), resp

    @utils.add_req_id_to_generator()
    def list(self, namespace, **kwargs):
        """Retrieve a listing of metadata tags.

        :returns: generator over list of tags.
        """
        url = '/v2/metadefs/namespaces/%(namespace)s/tags' % {
            'namespace': namespace}
        resp, body = self.http_client.get(url)

        for tag in body['tags']:
            yield self.model(tag), resp

    @utils.add_req_id_to_object()
    def delete(self, namespace, tag_name):
        """Delete a tag."""
        url = '/v2/metadefs/namespaces/%(namespace)s/tags/%(tag_name)s' % {
            'namespace': namespace, 'tag_name': tag_name}
        resp, body = self.http_client.delete(url)
        return (resp, body), resp

    @utils.add_req_id_to_object()
    def delete_all(self, namespace):
        """Delete all tags in a namespace."""
        url = '/v2/metadefs/namespaces/%(namespace)s/tags' % {
            'namespace': namespace}
        resp, body = self.http_client.delete(url)
        return (resp, body), resp
