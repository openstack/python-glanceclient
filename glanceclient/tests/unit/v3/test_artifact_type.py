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

import testtools

from glanceclient.tests.unit.v3 import get_artifact_fixture
from glanceclient.v3 import ArtifactType


class TestController(testtools.TestCase):
    def test_basic_create(self):
        """Create basic artifact without additional properties"""

        artifact = ArtifactType(**get_artifact_fixture())
        self.assertEqual("123", artifact.id)

    def test_additional_properties(self):
        """Create artifact with additional properties"""

        type_specific_properties = {"Lemongrab": 3,
                                    "Princess": "Bubblegum",
                                    "Candy people": ["Peppermint Butler",
                                                     "Starchie",
                                                     "Cinnamon Bun"]}
        artifact = ArtifactType(**get_artifact_fixture(
            **type_specific_properties))
        self.assertEqual(type_specific_properties,
                         artifact.type_specific_properties)

    def test_one_dependency(self):
        """Create artifact with one dependency"""

        inner_object = get_artifact_fixture(id="1000")
        artifact_fixture = get_artifact_fixture(dep=inner_object)
        artifact = ArtifactType(**artifact_fixture)
        self.assertEqual("1000", artifact.type_specific_properties['dep'].id)

    def test_list_dependencies(self):
        """Create artifact with a list of dependencies"""

        dependencies = [get_artifact_fixture(id=str(i)) for i in range(1000,
                                                                       1010)]

        artifact_fixture = get_artifact_fixture(dep_list=dependencies)
        artifact = ArtifactType(**artifact_fixture)
        self.assertEqual(10,
                         len(artifact.type_specific_properties['dep_list']))
        i = 1000
        for dep in artifact.type_specific_properties['dep_list']:
            self.assertEqual(str(i), dep.id)
            i += 1

    def test_invalid_dependency(self):
        """Create artifact with invalid dependency as a regular dict"""

        bad_inner_object = get_artifact_fixture(id="1000")
        del bad_inner_object['owner']
        good_inner_object = get_artifact_fixture(id="1001")

        artifact_fixture = get_artifact_fixture(bad_dep=bad_inner_object,
                                                good_dep=good_inner_object)
        artifact = ArtifactType(**artifact_fixture)
        self.assertIsInstance(artifact.type_specific_properties['bad_dep'],
                              dict)
        self.assertIsInstance(artifact.type_specific_properties['good_dep'],
                              ArtifactType)

    def test_invalid_dependencies_list(self):
        """Create artifact with list of dependencies with one invalid"""
        dependencies = [get_artifact_fixture(id=str(i)) for i in range(1000,
                                                                       1010)]

        del dependencies[9]['owner']
        artifact_fixture = get_artifact_fixture(bad_dep_list=dependencies)
        artifact = ArtifactType(**artifact_fixture)
        for dep in artifact.type_specific_properties['bad_dep_list']:
            self.assertIsInstance(dep, dict)
