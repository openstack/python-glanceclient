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

from oslo_utils import timeutils


def get_artifact_fixture(**kwargs):
    ts = timeutils.strtime()
    fixture = {
        "id": "123",
        "version": "11.2",
        "description": "by far, the most evil thing I've encountered",
        "name": "Gunter The Penguin",
        "visibility": "private",
        "state": "creating",
        "owner": "Ice King",
        "created_at": ts,
        "updated_at": ts,
        "deleted_at": None,
        "published_at": None,
        "tags": ["bottle", "egg"],
        "type_name": "ice_kingdom",
        "type_version": '1.0.1'
    }
    fixture.update(kwargs)
    return fixture
