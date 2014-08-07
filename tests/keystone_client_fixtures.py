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

import copy
import json
import uuid


# these are copied from python-keystoneclient tests
BASE_HOST = 'http://keystone.example.com'
BASE_URL = "%s:5000/" % BASE_HOST
UPDATED = '2013-03-06T00:00:00Z'

V2_URL = "%sv2.0" % BASE_URL
V2_DESCRIBED_BY_HTML = {'href': 'http://docs.openstack.org/api/'
                                'openstack-identity-service/2.0/content/',
                        'rel': 'describedby',
                        'type': 'text/html'}
V2_DESCRIBED_BY_PDF = {'href': 'http://docs.openstack.org/api/openstack-ident'
                               'ity-service/2.0/identity-dev-guide-2.0.pdf',
                       'rel': 'describedby',
                       'type': 'application/pdf'}

V2_VERSION = {'id': 'v2.0',
              'links': [{'href': V2_URL, 'rel': 'self'},
                        V2_DESCRIBED_BY_HTML, V2_DESCRIBED_BY_PDF],
              'status': 'stable',
              'updated': UPDATED}

V3_URL = "%sv3" % BASE_URL
V3_MEDIA_TYPES = [{'base': 'application/json',
                   'type': 'application/vnd.openstack.identity-v3+json'},
                  {'base': 'application/xml',
                   'type': 'application/vnd.openstack.identity-v3+xml'}]

V3_VERSION = {'id': 'v3.0',
              'links': [{'href': V3_URL, 'rel': 'self'}],
              'media-types': V3_MEDIA_TYPES,
              'status': 'stable',
              'updated': UPDATED}


def _create_version_list(versions):
    return json.dumps({'versions': {'values': versions}})


def _create_single_version(version):
    return json.dumps({'version': version})


V3_VERSION_LIST = _create_version_list([V3_VERSION, V2_VERSION])
V2_VERSION_LIST = _create_version_list([V2_VERSION])

V3_VERSION_ENTRY = _create_single_version(V3_VERSION)
V2_VERSION_ENTRY = _create_single_version(V2_VERSION)

GLANCE_ENDPOINT = 'http://glance.example.com/v1'


def _get_normalized_token_data(**kwargs):
    ref = copy.deepcopy(kwargs)
    # normalized token data
    ref['user_id'] = ref.get('user_id', uuid.uuid4().hex)
    ref['username'] = ref.get('username', uuid.uuid4().hex)
    ref['project_id'] = ref.get('project_id',
                                ref.get('tenant_id', uuid.uuid4().hex))
    ref['project_name'] = ref.get('tenant_name',
                                  ref.get('tenant_name', uuid.uuid4().hex))
    ref['user_domain_id'] = ref.get('user_domain_id', uuid.uuid4().hex)
    ref['user_domain_name'] = ref.get('user_domain_name', uuid.uuid4().hex)
    ref['project_domain_id'] = ref.get('project_domain_id', uuid.uuid4().hex)
    ref['project_domain_name'] = ref.get('project_domain_name',
                                         uuid.uuid4().hex)
    ref['roles'] = ref.get('roles', [{'name': uuid.uuid4().hex,
                                     'id': uuid.uuid4().hex}])
    ref['roles_link'] = ref.get('roles_link', [])
    ref['glance_url'] = ref.get('glance_url', GLANCE_ENDPOINT)

    return ref


def generate_v2_project_scoped_token(**kwargs):
    """Generate a Keystone V2 token based on auth request."""
    ref = _get_normalized_token_data(**kwargs)

    o = {'access': {'token': {'id': uuid.uuid4().hex,
                              'expires': '2099-05-22T00:02:43.941430Z',
                              'issued_at': '2013-05-21T00:02:43.941473Z',
                              'tenant': {'enabled': True,
                                         'id': ref.get('project_id'),
                                         'name': ref.get('project_id')
                                         }
                              },
                    'user': {'id': ref.get('user_id'),
                             'name': uuid.uuid4().hex,
                             'username': ref.get('username'),
                             'roles': ref.get('roles'),
                             'roles_links': ref.get('roles_links')
                             }
                    }}

    # we only care about Glance and Keystone endpoints
    o['access']['serviceCatalog'] = [
        {'endpoints': [
            {'publicURL': ref.get('glance_url'),
             'id': uuid.uuid4().hex,
             'region': 'RegionOne'
             }],
         'endpoints_links': [],
         'name': 'Glance',
         'type': 'keystore'},
        {'endpoints': [
            {'publicURL': ref.get('auth_url'),
             'adminURL': ref.get('auth_url'),
             'id': uuid.uuid4().hex,
             'region': 'RegionOne'
             }],
         'endpoint_links': [],
         'name': 'keystone',
         'type': 'identity'}]

    return o


def generate_v3_project_scoped_token(**kwargs):
    """Generate a Keystone V3 token based on auth request."""
    ref = _get_normalized_token_data(**kwargs)

    o = {'token': {'expires_at': '2099-05-22T00:02:43.941430Z',
                   'issued_at': '2013-05-21T00:02:43.941473Z',
                   'methods': ['password'],
                   'project': {'id': ref.get('project_id'),
                               'name': ref.get('project_name'),
                               'domain': {'id': ref.get('project_domain_id'),
                                          'name': ref.get(
                                              'project_domain_name')
                                          }
                               },
                   'user': {'id': ref.get('user_id'),
                            'name': ref.get('username'),
                            'domain': {'id': ref.get('user_domain_id'),
                                       'name': ref.get('user_domain_name')
                                       }
                            },
                   'roles': ref.get('roles')
                   }}

    # we only care about Glance and Keystone endpoints
    o['token']['catalog'] = [
        {'endpoints': [
            {
                'id': uuid.uuid4().hex,
                'interface': 'public',
                'region': 'RegionTwo',
                'url': ref.get('glance_url')
            }],
         'id': uuid.uuid4().hex,
         'type': 'keystore'},
        {'endpoints': [
            {
                'id': uuid.uuid4().hex,
                'interface': 'public',
                'region': 'RegionTwo',
                'url': ref.get('auth_url')
            },
            {
                'id': uuid.uuid4().hex,
                'interface': 'admin',
                'region': 'RegionTwo',
                'url': ref.get('auth_url')
            }],
         'id': uuid.uuid4().hex,
         'type': 'identity'}]

    # token ID is conveyed via the X-Subject-Token header so we are generating
    # one to stash there
    token_id = uuid.uuid4().hex

    return token_id, o
