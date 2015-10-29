# Copyright 2015 OpenStack Foundation
# Copyright 2015 Huawei Corp.
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
from glanceclient.v2 import versions

fixtures = {
    '/versions': {
        'GET': (
            {},
            {"versions": [
                {
                    "status": "EXPERIMENTAL",
                    "id": "v3.0",
                    "links": [
                        {
                            "href": "http://10.229.45.145:9292/v3/",
                            "rel": "self"
                        }
                    ]
                },
                {
                    "status": "CURRENT",
                    "id": "v2.3",
                    "links": [
                        {
                            "href": "http://10.229.45.145:9292/v2/",
                            "rel": "self"
                        }
                    ]
                },
                {
                    "status": "SUPPORTED",
                    "id": "v1.0",
                    "links": [
                        {
                            "href": "http://10.229.45.145:9292/v1/",
                            "rel": "self"
                        }
                    ]
                }
            ]}
        )
    }
}


class TestVersions(testtools.TestCase):

    def setUp(self):
        super(TestVersions, self).setUp()
        self.api = utils.FakeAPI(fixtures)
        self.controller = versions.VersionController(self.api)

    def test_version_list(self):
        version = list(self.controller.list())
        self.assertEqual('v3.0', version[0]['id'])
        self.assertEqual('EXPERIMENTAL', version[0]['status'])
        self.assertEqual([{"href": "http://10.229.45.145:9292/v3/",
                           "rel": "self"}], version[0]['links'])
