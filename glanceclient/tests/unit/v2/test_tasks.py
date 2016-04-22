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

from glanceclient.tests.unit.v2 import base
from glanceclient.tests import utils
from glanceclient.v2 import tasks


_OWNED_TASK_ID = 'a4963502-acc7-42ba-ad60-5aa0962b7faf'
_OWNER_ID = '6bd473f0-79ae-40ad-a927-e07ec37b642f'
_FAKE_OWNER_ID = '63e7f218-29de-4477-abdc-8db7c9533188'
_PENDING_ID = '3a4560a1-e585-443e-9b39-553b46ec92d1'
_PROCESSING_ID = '6f99bf80-2ee6-47cf-acfe-1f1fabb7e810'


fixtures = {
    '/v2/tasks?limit=%d' % tasks.DEFAULT_PAGE_SIZE: {
        'GET': (
            {},
            {'tasks': [
                {
                    'id': _PENDING_ID,
                    'type': 'import',
                    'status': 'pending',
                },
                {
                    'id': _PROCESSING_ID,
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
                        'id': _PENDING_ID,
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
                    'id': _PROCESSING_ID,
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
                'id': _PENDING_ID,
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
                'id': _PENDING_ID,
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
    },
    '/v2/tasks?limit=%d&sort_key=type' % tasks.DEFAULT_PAGE_SIZE: {
        'GET': (
            {},
            {'tasks': [
                {
                    'id': _PENDING_ID,
                    'type': 'import',
                    'status': 'pending',
                },
                {
                    'id': _PROCESSING_ID,
                    'type': 'import',
                    'status': 'processing',
                },
            ]},
        ),
    },
    '/v2/tasks?limit=%d&sort_dir=asc&sort_key=id' % tasks.DEFAULT_PAGE_SIZE: {
        'GET': (
            {},
            {'tasks': [
                {
                    'id': _PENDING_ID,
                    'type': 'import',
                    'status': 'pending',
                },
                {
                    'id': _PROCESSING_ID,
                    'type': 'import',
                    'status': 'processing',
                },
            ]},
        ),
    },
    '/v2/tasks?limit=%d&sort_dir=desc&sort_key=id' % tasks.DEFAULT_PAGE_SIZE: {
        'GET': (
            {},
            {'tasks': [
                {
                    'id': _PROCESSING_ID,
                    'type': 'import',
                    'status': 'processing',
                },
                {
                    'id': _PENDING_ID,
                    'type': 'import',
                    'status': 'pending',
                },
            ]},
        ),
    },
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
        self.controller = base.BaseController(self.api, self.schema_api,
                                              tasks.Controller)

    def test_list_tasks(self):
        tasks = self.controller.list()
        self.assertEqual(_PENDING_ID, tasks[0].id)
        self.assertEqual('import', tasks[0].type)
        self.assertEqual('pending', tasks[0].status)
        self.assertEqual(_PROCESSING_ID, tasks[1].id)
        self.assertEqual('import', tasks[1].type)
        self.assertEqual('processing', tasks[1].status)

    def test_list_tasks_paginated(self):
        tasks = self.controller.list(page_size=1)
        self.assertEqual(_PENDING_ID, tasks[0].id)
        self.assertEqual('import', tasks[0].type)
        self.assertEqual(_PROCESSING_ID, tasks[1].id)
        self.assertEqual('import', tasks[1].type)

    def test_list_tasks_with_status(self):
        filters = {'filters': {'status': 'processing'}}
        tasks = self.controller.list(**filters)
        self.assertEqual(_OWNED_TASK_ID, tasks[0].id)

    def test_list_tasks_with_wrong_status(self):
        filters = {'filters': {'status': 'fake'}}
        tasks = self.controller.list(**filters)
        self.assertEqual(0, len(tasks))

    def test_list_tasks_with_type(self):
        filters = {'filters': {'type': 'import'}}
        tasks = self.controller.list(**filters)
        self.assertEqual(_OWNED_TASK_ID, tasks[0].id)

    def test_list_tasks_with_wrong_type(self):
        filters = {'filters': {'type': 'fake'}}
        tasks = self.controller.list(**filters)
        self.assertEqual(0, len(tasks))

    def test_list_tasks_for_owner(self):
        filters = {'filters': {'owner': _OWNER_ID}}
        tasks = self.controller.list(**filters)
        self.assertEqual(_OWNED_TASK_ID, tasks[0].id)

    def test_list_tasks_for_fake_owner(self):
        filters = {'filters': {'owner': _FAKE_OWNER_ID}}
        tasks = self.controller.list(**filters)
        self.assertEqual(tasks, [])

    def test_list_tasks_filters_encoding(self):
        filters = {"owner": u"ni\xf1o"}
        try:
            self.controller.list(filters=filters)
        except KeyError:
            # NOTE(flaper87): It raises KeyError because there's
            # no fixture supporting this query:
            #   /v2/tasks?owner=ni%C3%B1o&limit=20
            # We just want to make sure filters are correctly encoded.
            pass

        self.assertEqual(b"ni\xc3\xb1o", filters["owner"])

    def test_list_tasks_with_marker(self):
        tasks = self.controller.list(marker=_PENDING_ID, page_size=1)
        self.assertEqual(1, len(tasks))
        self.assertEqual(_PROCESSING_ID, tasks[0]['id'])

    def test_list_tasks_with_single_sort_key(self):
        tasks = self.controller.list(sort_key='type')
        self.assertEqual(2, len(tasks))
        self.assertEqual(_PENDING_ID, tasks[0].id)

    def test_list_tasks_with_invalid_sort_key(self):
        self.assertRaises(ValueError,
                          self.controller.list, sort_key='invalid')

    def test_list_tasks_with_desc_sort_dir(self):
        tasks = self.controller.list(sort_key='id', sort_dir='desc')
        self.assertEqual(2, len(tasks))
        self.assertEqual(_PENDING_ID, tasks[1].id)

    def test_list_tasks_with_asc_sort_dir(self):
        tasks = self.controller.list(sort_key='id', sort_dir='asc')
        self.assertEqual(2, len(tasks))
        self.assertEqual(_PENDING_ID, tasks[0].id)

    def test_list_tasks_with_invalid_sort_dir(self):
        self.assertRaises(ValueError,
                          self.controller.list,
                          sort_dir='invalid')

    def test_get_task(self):
        task = self.controller.get(_PENDING_ID)
        self.assertEqual(_PENDING_ID, task.id)
        self.assertEqual('import', task.type)

    def test_create_task(self):
        properties = {
            'type': 'import',
            'input': {'import_from_format': 'ovf', 'import_from':
                      'swift://cloud.foo/myaccount/mycontainer/path'},
        }
        task = self.controller.create(**properties)
        self.assertEqual(_PENDING_ID, task.id)
        self.assertEqual('import', task.type)

    def test_create_task_invalid_property(self):
        properties = {
            'type': 'import',
            'bad_prop': 'value',
        }
        self.assertRaises(TypeError, self.controller.create, **properties)
