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
import errno
import testtools

from glanceclient import exc
from glanceclient.tests.unit.v3 import get_artifact_fixture
from glanceclient.tests import utils
from glanceclient.v3 import artifacts


type_fixture = {'type_name': 'adventure_time', 'type_version': '1.0.2'}

data_fixtures = {
    '/v3/artifacts/ice_kingdom/v1.0.1/drafts': {
        'POST': (
            {},
            get_artifact_fixture(id='3a4560a1-e585-443e-9b39-553b46ec92d1',
                                 name='LSP',
                                 version='0.0.1')
        ),
    },
    '/v3/artifacts/ice_kingdom/v1.0.1/87b634c1-f893-33c9-28a9-e5673c99239a': {
        'DELETE': (
            {},
            {
                'id': '87b634c1-f893-33c9-28a9-e5673c99239a',
            },
        ),
        'GET': (
            {},
            get_artifact_fixture(id='87b634c1-f893-33c9-28a9-e5673c99239a'),
        ),
    },
    '/v3/artifacts/ice_kingdom/v1.0.1/'
    '87b634c1-f893-33c9-28a9-e5673c99239a?show_level=none': {
        'GET': (
            {},
            get_artifact_fixture(id='87b634c1-f893-33c9-28a9-e5673c99239a',
                                 version='3123.0'),
        ),
    },
    '/v3/artifacts/adventure_time/v1.0.2/'
    '3a4560a1-e585-443e-9b39-553b46ec92d1': {
        'GET': (
            {},
            get_artifact_fixture(id='3a4560a1-e585-443e-9b39-553b46ec92d1',
                                 finn=None, **type_fixture),
        ),
        'PATCH': (
            {},
            get_artifact_fixture(id='3a4560a1-e585-443e-9b39-553b46ec92d1',
                                 finn='human', **type_fixture)
        ),
    },
    '/v3/artifacts/adventure_time/v1.0.2/'
    '4cd6da69-1f08-45f0-af22-a06f3106588f': {
        'GET': (
            {},
            get_artifact_fixture(id='4cd6da69-1f08-45f0-af22-a06f3106588f',
                                 finn='dog', **type_fixture),
        ),
        'PATCH': (
            {},
            get_artifact_fixture(id='4cd6da69-1f08-45f0-af22-a06f3106588f',
                                 finn='human', **type_fixture)
        ),
    },
    '/v3/artifacts/adventure_time/v1.0.2/'
    '55f2bcf0-f34d-4c06-bb67-fa43b439ab20': {
        'GET': (
            {},
            get_artifact_fixture(id='55f2bcf0-f34d-4c06-bb67-fa43b439ab20',
                                 finn='human', **type_fixture),
        ),
        'PATCH': (
            {},
            get_artifact_fixture(id='55f2bcf0-f34d-4c06-bb67-fa43b439ab20',
                                 **type_fixture)
        ),
    },
    '/v3/artifacts/adventure_time/v1.0.2/'
    '73a0ebdd-6b32-4536-a529-c8301f2af2c6': {
        'GET': (
            {},
            get_artifact_fixture(id='73a0ebdd-6b32-4536-a529-c8301f2af2c6',
                                 **type_fixture),
        ),
        'PATCH': (
            {},
            get_artifact_fixture(id='73a0ebdd-6b32-4536-a529-c8301f2af2c6',
                                 name='Marceline', **type_fixture)
        ),
    },
    '/v3/artifacts/adventure_time/v1.0.2/'
    'c859cae3-d924-45b7-a0da-fcc30ad9c6ab': {
        'GET': (
            {},
            get_artifact_fixture(id='c859cae3-d924-45b7-a0da-fcc30ad9c6ab',
                                 **type_fixture)
        ),
    },
    '/v3/artifacts/adventure_time/v1.0.2/'
    '9dcbafea-ebea-40a8-8f4b-5c54d6d58e1f': {
        'GET': (
            {},
            get_artifact_fixture(id='9dcbafea-ebea-40a8-8f4b-5c54d6d58e1f',
                                 finn='dog', **type_fixture),
        ),
        'PATCH': (
            {},
            get_artifact_fixture(id='9dcbafea-ebea-40a8-8f4b-5c54d6d58e1f',
                                 finn='human', **type_fixture)
        ),
    },
    '/v3/artifacts/adventure_time/v1.0.2/'
    '18f67e12-88e0-4b13-86fb-5adc36d884b6/image_file': {
        'PUT': (
            {},
            '',
        ),

        'DELETE': (
            {},
            '',
        ),
    },
    '/v3/artifacts/adventure_time/v1.0.2/'
    '18f67e12-88e0-4b13-86fb-5adc36d884b6/image_file/download': {
        'GET': (
            {},
            'Princess Bubblegum rocks!!!',
        ),
    },
    '/v3/artifacts/adventure_time/v1.0.2/'
    '5cc4bebc-db27-11e1-a1eb-080027cbe205/image_file/download': {
        'GET': (
            {
                'content-md5': '5a3c872ee92e2c58efd0d47862eb9c85'
            },
            'Princess Bubblegum rocks!!!',
        ),
    },
    '/v3/artifacts/adventure_time/v1.0.2/'
    '66fb18d6-db27-11e1-a1eb-080027cbe205/image_file/download': {
        'GET': (
            {
                'content-md5': 'Lich was here!!!'
            },
            'Princess Bubblegum rocks!!!',
        ),
    },
    '/v3/artifacts/adventure_time/v1.0.2/'
    '18f67e12-88e0-4b13-86fb-5adc36d884b6/screenshots/1': {
        'PUT': (
            {},
            '',
        ),

        'DELETE': (
            {},
            '',
        ),
    },
    '/v3/artifacts/adventure_time/v1.0.2/'
    '18f67e12-88e0-4b13-86fb-5adc36d884b6/screenshots/1/download': {
        'GET': (
            {},
            'What time is it?',
        ),
    },

}


class TestController(testtools.TestCase):
    def setUp(self):
        super(TestController, self).setUp()
        self.api = utils.FakeAPI(data_fixtures)
        self.controller = artifacts.Controller(self.api)

    def test_create_artifact(self):
        artifact_fixture = get_artifact_fixture(name='LSP',
                                                version='0.0.1')
        artifact = self.controller.create(**artifact_fixture)
        self.assertEqual('3a4560a1-e585-443e-9b39-553b46ec92d1',
                         artifact.id)
        self.assertEqual('LSP', artifact.name)
        self.assertEqual('0.0.1', artifact.version)

    def test_create_artifact_no_type_version(self):
        artifact_fixture = get_artifact_fixture(name='artifact-1',
                                                version='0.0.1')
        del artifact_fixture['type_version']
        self.assertRaises(exc.HTTPBadRequest, self.controller.create,
                          **artifact_fixture)

    def test_create_artifact_no_type_name(self):
        artifact_fixture = get_artifact_fixture(name='artifact-1',
                                                version='0.0.1')
        del artifact_fixture['type_name']
        self.assertRaises(exc.HTTPBadRequest, self.controller.create,
                          **artifact_fixture)

    def test_delete_artifact(self):
        artifact_id = '87b634c1-f893-33c9-28a9-e5673c99239a'

        self.controller.delete(artifact_id, 'ice_kingdom', '1.0.1')
        expect = [
            ('DELETE',
                '/v3/artifacts/ice_kingdom/v1.0.1/%s' % artifact_id,
                {},
                None)]
        self.assertEqual(expect, self.api.calls)

    def test_get_artifact(self):
        artifact_id = '87b634c1-f893-33c9-28a9-e5673c99239a'

        artifact = self.controller.get(artifact_id, 'ice_kingdom', '1.0.1')
        self.assertEqual('Gunter The Penguin', artifact.name)
        self.assertEqual('11.2', artifact.version)

    def test_get_artifact_show_level(self):
        artifact_id = '87b634c1-f893-33c9-28a9-e5673c99239a'
        show_level = 'none'
        artifact = self.controller.get(artifact_id, 'ice_kingdom', '1.0.1',
                                       show_level)
        self.assertEqual('Gunter The Penguin', artifact.name)
        self.assertEqual('3123.0', artifact.version)

    def test_get_artifact_invalid_show_level(self):
        artifact_id = '87b634c1-f893-33c9-28a9-e5673c99239a'
        show_level = 'invalid'
        self.assertRaises(exc.HTTPBadRequest, self.controller.get,
                          artifact_id, 'ice_kingdom', '1.0.1', show_level)

    def test_update_add_custom_prop(self):
        artifact_id = '3a4560a1-e585-443e-9b39-553b46ec92d1'

        artifact = self.controller.update(artifact_id, finn='human',
                                          **type_fixture)
        expect_hdrs = {
            'Content-Type': 'application/openstack-images-v2.1-json-patch',
        }
        expect_body = [{'op': 'add', 'path': '/finn', 'value': 'human'}]
        expect = [
            ('GET', '/v3/artifacts/adventure_time/v1.0.2/'
                    '%s' % artifact_id, {}, None),
            ('PATCH', '/v3/artifacts/adventure_time/v1.0.2/'
                      '%s' % artifact_id, expect_hdrs, expect_body),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(artifact_id, artifact.id)
        self.assertEqual('Gunter The Penguin', artifact.name)
        self.assertEqual('human', artifact.type_specific_properties['finn'])

    def test_update_replace_custom_prop(self):
        artifact_id = '4cd6da69-1f08-45f0-af22-a06f3106588f'

        artifact = self.controller.update(artifact_id, finn='human',
                                          **type_fixture)
        expect_hdrs = {
            'Content-Type': 'application/openstack-images-v2.1-json-patch',
        }
        expect_body = [{'op': 'replace', 'path': '/finn', 'value': 'human'}]
        expect = [
            ('GET', '/v3/artifacts/adventure_time/v1.0.2/'
                    '%s' % artifact_id, {}, None),
            ('PATCH', '/v3/artifacts/adventure_time/v1.0.2/'
                      '%s' % artifact_id, expect_hdrs, expect_body),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(artifact_id, artifact.id)
        self.assertEqual('Gunter The Penguin', artifact.name)
        self.assertEqual('human', artifact.type_specific_properties['finn'])

    def test_update_delete_custom_prop(self):
        artifact_id = '55f2bcf0-f34d-4c06-bb67-fa43b439ab20'

        artifact = self.controller.update(artifact_id, remove_props=['finn'],
                                          **type_fixture)
        expect_hdrs = {
            'Content-Type': 'application/openstack-images-v2.1-json-patch',
        }
        expect_body = [{'op': 'remove', 'path': '/finn'}]
        expect = [
            ('GET', '/v3/artifacts/adventure_time/v1.0.2/'
                    '%s' % artifact_id, {}, None),
            ('PATCH', '/v3/artifacts/adventure_time/v1.0.2/'
                      '%s' % artifact_id, expect_hdrs, expect_body),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(artifact_id, artifact.id)
        self.assertEqual('Gunter The Penguin', artifact.name)
        self.assertNotIn('finn', artifact.type_specific_properties)

    def test_update_replace_base_prop(self):
        artifact_id = '73a0ebdd-6b32-4536-a529-c8301f2af2c6'

        artifact = self.controller.update(artifact_id, name='Marceline',
                                          **type_fixture)
        expect_hdrs = {
            'Content-Type': 'application/openstack-images-v2.1-json-patch',
        }
        expect_body = [{'op': 'replace', 'path': '/name',
                        'value': 'Marceline'}]
        expect = [
            ('GET', '/v3/artifacts/adventure_time/v1.0.2/'
                    '%s' % artifact_id, {}, None),
            ('PATCH', '/v3/artifacts/adventure_time/v1.0.2/'
                      '%s' % artifact_id, expect_hdrs, expect_body),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(artifact_id, artifact.id)
        self.assertEqual('Marceline', artifact.name)

    def test_update_remove_base_prop(self):
        artifact_id = '73a0ebdd-6b32-4536-a529-c8301f2af2c6'

        self.assertRaises(exc.HTTPBadRequest, self.controller.update,
                          artifact_id, remove_props=['name'], **type_fixture)

    def test_update_add_nonexiting_property(self):
        artifact_id = 'c859cae3-d924-45b7-a0da-fcc30ad9c6ab'

        self.assertRaises(exc.HTTPBadRequest, self.controller.update,
                          artifact_id, finn='human', **type_fixture)

    def test_remove_and_replace_same_property(self):
        artifact_id = '9dcbafea-ebea-40a8-8f4b-5c54d6d58e1f'

        artifact = self.controller.update(artifact_id, finn='human',
                                          remove_props=['finn'],
                                          **type_fixture)
        expect_hdrs = {
            'Content-Type': 'application/openstack-images-v2.1-json-patch',
        }
        expect_body = [{'op': 'replace', 'path': '/finn', 'value': 'human'}]
        expect = [
            ('GET', '/v3/artifacts/adventure_time/v1.0.2/'
                    '%s' % artifact_id, {}, None),
            ('PATCH', '/v3/artifacts/adventure_time/v1.0.2/'
                      '%s' % artifact_id, expect_hdrs, expect_body),
        ]
        self.assertEqual(expect, self.api.calls)
        self.assertEqual(artifact_id, artifact.id)
        self.assertEqual('Gunter The Penguin', artifact.name)
        self.assertEqual('human', artifact.type_specific_properties['finn'])

    def test_upload_blob(self):
        image_data = 'Adventure Time with Finn & Jake'

        artifact_id = '18f67e12-88e0-4b13-86fb-5adc36d884b6'

        params = {'blob_property': 'image_file', 'artifact_id': artifact_id,
                  'data': image_data}
        params.update(type_fixture)

        self.controller.upload_blob(**params)
        expect_hdrs = {'Content-Type': 'application/octet-stream'}
        expect = [('PUT', '/v3/artifacts/adventure_time/v1.0.2/'
                   '%s/image_file' % artifact_id, expect_hdrs, image_data)]

        self.assertEqual(expect, self.api.calls)

    def test_delete_blob(self):
        artifact_id = '18f67e12-88e0-4b13-86fb-5adc36d884b6'

        params = {'blob_property': 'image_file', 'artifact_id': artifact_id}
        params.update(type_fixture)
        self.controller.delete_blob(**params)
        expect = [('DELETE', '/v3/artifacts/adventure_time/v1.0.2/'
                   '%s/image_file' % artifact_id, {}, None)]

        self.assertEqual(expect, self.api.calls)

    def test_download_blob(self):
        artifact_id = '18f67e12-88e0-4b13-86fb-5adc36d884b6'

        params = {'blob_property': 'image_file', 'artifact_id': artifact_id}
        params.update(type_fixture)
        body = ''.join([b for b in self.controller.download_blob(**params)])

        expect = [('GET', '/v3/artifacts/adventure_time/v1.0.2/'
                   '%s/image_file/download' % artifact_id, {}, None)]

        self.assertEqual(expect, self.api.calls)
        self.assertEqual('Princess Bubblegum rocks!!!', body)

    def test_download_blob_with_checksum(self):
        artifact_id = '5cc4bebc-db27-11e1-a1eb-080027cbe205'
        params = {'blob_property': 'image_file', 'artifact_id': artifact_id}
        params.update(type_fixture)
        body = ''.join([b for b in self.controller.download_blob(**params)])

        self.assertEqual('Princess Bubblegum rocks!!!', body)

        params['do_checksum'] = False
        body = ''.join([b for b in self.controller.download_blob(**params)])

        expect = [('GET', '/v3/artifacts/adventure_time/v1.0.2/'
                   '%s/image_file/download' % artifact_id, {}, None)] * 2

        self.assertEqual(expect, self.api.calls)
        self.assertEqual('Princess Bubblegum rocks!!!', body)

    def test_download_blob_with_wrong_checksum(self):
        artifact_id = '66fb18d6-db27-11e1-a1eb-080027cbe205'

        params = {'blob_property': 'image_file', 'artifact_id': artifact_id}
        params.update(type_fixture)
        try:
            ''.join([b for b in self.controller.download_blob(**params)])
            self.fail('data did not raise an error.')
        except IOError as e:
            self.assertEqual(errno.EPIPE, e.errno)
            msg = 'was 5a3c872ee92e2c58efd0d47862eb9c85 expected Lich'
            self.assertIn(msg, str(e))

        params['do_checksum'] = False
        body = ''.join([b for b in self.controller.download_blob(**params)])

        expect = [('GET', '/v3/artifacts/adventure_time/v1.0.2/'
                   '%s/image_file/download' % artifact_id, {}, None)] * 2

        self.assertEqual(expect, self.api.calls)
        self.assertEqual('Princess Bubblegum rocks!!!', body)

    def test_data_upload_blob_with_position(self):
        image_data = 'Adventure Time with Finn & Jake'

        artifact_id = '18f67e12-88e0-4b13-86fb-5adc36d884b6'

        params = {'blob_property': 'screenshots', 'artifact_id': artifact_id,
                  'position': 1, 'data': image_data}
        params.update(type_fixture)

        self.controller.upload_blob(**params)
        expect_hdrs = {'Content-Type': 'application/octet-stream'}
        expect = [('PUT', '/v3/artifacts/adventure_time/v1.0.2/'
                   '%s/screenshots/1' % artifact_id, expect_hdrs, image_data)]

        self.assertEqual(expect, self.api.calls)

    def test_delete_blob_with_position(self):
        artifact_id = '18f67e12-88e0-4b13-86fb-5adc36d884b6'

        params = {'blob_property': 'screenshots', 'artifact_id': artifact_id,
                  'position': 1}
        params.update(type_fixture)
        self.controller.delete_blob(**params)
        expect = [('DELETE', '/v3/artifacts/adventure_time/v1.0.2/'
                   '%s/screenshots/1' % artifact_id, {}, None)]

        self.assertEqual(expect, self.api.calls)

    def test_download_blob_with_position(self):
        artifact_id = '18f67e12-88e0-4b13-86fb-5adc36d884b6'

        params = {'blob_property': 'screenshots', 'artifact_id': artifact_id,
                  'position': 1}
        params.update(type_fixture)
        body = ''.join([b for b in self.controller.download_blob(**params)])
        expect = [('GET', '/v3/artifacts/adventure_time/v1.0.2/'
                   '%s/screenshots/1/download' % artifact_id, {}, None)]

        self.assertEqual(expect, self.api.calls)
        self.assertEqual('What time is it?', body)
