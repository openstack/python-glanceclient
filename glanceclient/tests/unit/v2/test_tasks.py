# Copyright 2013 OpenStack Foundation.
# Copyright 2013 IBM Corp.
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

import testtools

from glanceclient.tests import utils
from glanceclient.v2 import tasks


_OWNED_TASK_ID = 'a4963502-acc7-42ba-ad60-5aa0962b7faf'
_OWNER_ID = '6bd473f0-79ae-40ad-a927-e07ec37b642f'
_FAKE_OWNER_ID = '63e7f218-29de-4477-abdc-8db7c9533188'


fixtures = {
    '/v2/tasks?limit=%d' % tasks.DEFAULT_PAGE_SIZE: {
        'GET': (
            {},
            {'tasks': [
                {
                    'id': '3a4560a1-e585-443e-9b39-553b46ec92d1',
                    'type': 'import',
                    'status': 'pending',
                },
                {
                    'id': '6f99bf80-2ee6-47cf-acfe-1f1fabb7e810',
                    'type': 'import',
                    'status': 'processing',
                },
            ]},
        ),
    },
    '/v2/tasks?limit=1': {
        'GET': (
            {},
            {
                'tasks': [
                    {
                        'id': '3a4560a1-e585-443e-9b39-553b46ec92d1',
                        'type': 'import',
                        'status': 'pending',
                    },
                ],
                'next': ('/v2/tasks?limit=1&'
                         'marker=3a4560a1-e585-443e-9b39-553b46ec92d1'),
            },
        ),
    },
    ('/v2/tasks?limit=1&marker=3a4560a1-e585-443e-9b39-553b46ec92d1'): {
        'GET': (
            {},
            {'tasks': [
                {
                    'id': '6f99bf80-2ee6-47cf-acfe-1f1fabb7e810',
                    'type': 'import',
                    'status': 'pending',
                },
            ]},
        ),
    },
    '/v2/tasks/3a4560a1-e585-443e-9b39-553b46ec92d1': {
        'GET': (
            {},
            {
                'id': '3a4560a1-e585-443e-9b39-553b46ec92d1',
                'type': 'import',
                'status': 'pending',
            },
        ),
        'PATCH': (
            {},
            '',
        ),
    },
    '/v2/tasks/e7e59ff6-fa2e-4075-87d3-1a1398a07dc3': {
        'GET': (
            {},
            {
                'id': 'e7e59ff6-fa2e-4075-87d3-1a1398a07dc3',
                'type': 'import',
                'status': 'pending',
            },
        ),
        'PATCH': (
            {},
            '',
        ),
    },
    '/v2/tasks': {
        'POST': (
            {},
            {
                'id': '3a4560a1-e585-443e-9b39-553b46ec92d1',
                'type': 'import',
                'status': 'pending',
                'input': '{"import_from": "file:///", '
                '"import_from_format": "qcow2"}'
            },
        ),
    },
    '/v2/tasks?limit=%d&owner=%s' % (tasks.DEFAULT_PAGE_SIZE, _OWNER_ID): {
        'GET': (
            {},
            {'tasks': [
                {
                    'id': _OWNED_TASK_ID,
                },
            ]},
        ),
    },
    '/v2/tasks?limit=%d&status=processing' % (tasks.DEFAULT_PAGE_SIZE): {
        'GET': (
            {},
            {'tasks': [
                {
                    'id': _OWNED_TASK_ID,
                },
            ]},
        ),
    },
    '/v2/tasks?limit=%d&type=import' % (tasks.DEFAULT_PAGE_SIZE): {
        'GET': (
            {},
            {'tasks': [
                {
                    'id': _OWNED_TASK_ID,
                },
            ]},
        ),
    },
    '/v2/tasks?limit=%d&type=fake' % (tasks.DEFAULT_PAGE_SIZE): {
        'GET': (
            {},
            {'tasks': [
            ]},
        ),
    },
    '/v2/tasks?limit=%d&status=fake' % (tasks.DEFAULT_PAGE_SIZE): {
        'GET': (
            {},
            {'tasks': [
            ]},
        ),
    },
    '/v2/tasks?limit=%d&type=import' % (tasks.DEFAULT_PAGE_SIZE): {
        'GET': (
            {},
            {'tasks': [
                {
                    'id': _OWNED_TASK_ID,
                },
            ]},
        ),
    },
    '/v2/tasks?limit=%d&owner=%s' % (tasks.DEFAULT_PAGE_SIZE, _FAKE_OWNER_ID):
    {
        'GET': ({},
                {'tasks': []},
                ),
    }
}

schema_fixtures = {
    'task': {
        'GET': (
            {},
            {
                'name': 'task',
                'properties': {
                    'id': {},
                    'type': {},
                    'status': {},
                    'input': {},
                    'result': {},
                    'message': {},
                },
                'additionalProperties': False,
            }
        )
    }
}


class TestController(testtools.TestCase):
    def setUp(self):
        super(TestController, self).setUp()
        self.api = utils.FakeAPI(fixtures)
        self.schema_api = utils.FakeSchemaAPI(schema_fixtures)
        self.controller = tasks.Controller(self.api, self.schema_api)

    def test_list_tasks(self):
        #NOTE(flwang): cast to list since the controller returns a generator
        tasks = list(self.controller.list())
        self.assertEqual(tasks[0].id, '3a4560a1-e585-443e-9b39-553b46ec92d1')
        self.assertEqual(tasks[0].type, 'import')
        self.assertEqual(tasks[0].status, 'pending')
        self.assertEqual(tasks[1].id, '6f99bf80-2ee6-47cf-acfe-1f1fabb7e810')
        self.assertEqual(tasks[1].type, 'import')
        self.assertEqual(tasks[1].status, 'processing')

    def test_list_tasks_paginated(self):
        #NOTE(flwang): cast to list since the controller returns a generator
        tasks = list(self.controller.list(page_size=1))
        self.assertEqual(tasks[0].id, '3a4560a1-e585-443e-9b39-553b46ec92d1')
        self.assertEqual(tasks[0].type, 'import')
        self.assertEqual(tasks[1].id, '6f99bf80-2ee6-47cf-acfe-1f1fabb7e810')
        self.assertEqual(tasks[1].type, 'import')

    def test_list_tasks_with_status(self):
        filters = {'filters': {'status': 'processing'}}
        tasks = list(self.controller.list(**filters))
        self.assertEqual(tasks[0].id, _OWNED_TASK_ID)

    def test_list_tasks_with_wrong_status(self):
        filters = {'filters': {'status': 'fake'}}
        tasks = list(self.controller.list(**filters))
        self.assertEqual(len(tasks), 0)

    def test_list_tasks_with_type(self):
        filters = {'filters': {'type': 'import'}}
        tasks = list(self.controller.list(**filters))
        self.assertEqual(tasks[0].id, _OWNED_TASK_ID)

    def test_list_tasks_with_wrong_type(self):
        filters = {'filters': {'type': 'fake'}}
        tasks = list(self.controller.list(**filters))
        self.assertEqual(len(tasks), 0)

    def test_list_tasks_for_owner(self):
        filters = {'filters': {'owner': _OWNER_ID}}
        tasks = list(self.controller.list(**filters))
        self.assertEqual(tasks[0].id, _OWNED_TASK_ID)

    def test_list_tasks_for_fake_owner(self):
        filters = {'filters': {'owner': _FAKE_OWNER_ID}}
        tasks = list(self.controller.list(**filters))
        self.assertEqual(tasks, [])

    def test_list_tasks_filters_encoding(self):
        filters = {"owner": u"ni\xf1o"}
        try:
            list(self.controller.list(filters=filters))
        except KeyError:
            # NOTE(flaper87): It raises KeyError because there's
            # no fixture supporting this query:
            #   /v2/tasks?owner=ni%C3%B1o&limit=20
            # We just want to make sure filters are correctly encoded.
            pass

        self.assertEqual(b"ni\xc3\xb1o", filters["owner"])

    def test_get_task(self):
        task = self.controller.get('3a4560a1-e585-443e-9b39-553b46ec92d1')
        self.assertEqual(task.id, '3a4560a1-e585-443e-9b39-553b46ec92d1')
        self.assertEqual(task.type, 'import')

    def test_create_task(self):
        properties = {
            'type': 'import',
            'input': {'import_from_format': 'ovf', 'import_from':
                      'swift://cloud.foo/myaccount/mycontainer/path'},
        }
        task = self.controller.create(**properties)
        self.assertEqual(task.id, '3a4560a1-e585-443e-9b39-553b46ec92d1')
        self.assertEqual(task.type, 'import')

    def test_create_task_invalid_property(self):
        properties = {
            'type': 'import',
            'bad_prop': 'value',
        }
        self.assertRaises(TypeError, self.controller.create, **properties)
