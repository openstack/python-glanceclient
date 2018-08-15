# Copyright 2015 OpenStack Foundation
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


# NOTE(flaper87): Keep a copy of the current default schema so that
# we can react on cases where there's no connection to an OpenStack
# deployment. See #1481729
BASE_SCHEMA = {
    "additionalProperties": False,
    "required": ["name"],
    "name": "resource_type_association",
    "properties": {
        "name": {
            "type": "string",
            "description": "Resource type names should be aligned with Heat "
                           "resource types whenever possible: https://docs."
                           "openstack.org/heat/latest/template_guide/"
                           "openstack.html",
            "maxLength": 80

        },
        "prefix": {
            "type": "string",
            "description": "Specifies the prefix to use for the given resource"
                           " type. Any properties in the namespace should be"
                           " prefixed with this prefix when being applied to"
                           " the specified resource type. Must include prefix"
                           " separator (e.g. a colon :).",
            "maxLength": 80
        },
        "properties_target": {
            "type": "string",
            "description": "Some resource types allow more than one key / "
                           "value pair per instance.  For example, Cinder "
                           "allows user and image metadata on volumes. Only "
                           "the image properties metadata is evaluated by Nova"
                           " (scheduling or drivers). This property allows a "
                           "namespace target to remove the ambiguity.",
            "maxLength": 80
        },
        "created_at": {
            "type": "string",
            "readOnly": True,
            "description": "Date and time of resource type association.",
            "format": "date-time"
        },
        "updated_at": {
            "type": "string",
            "readOnly": True,
            "description": "Date and time of the last resource type "
                           "association modification.",
            "format": "date-time"
        }
    }
}
