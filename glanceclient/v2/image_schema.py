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

_doc_url = "http://docs.openstack.org/trunk/openstack-compute/admin/content/adding-images.html"  # noqa
# NOTE(flaper87): Keep a copy of the current default schema so that
# we can react on cases where there's no connection to an OpenStack
# deployment. See #1481729
_BASE_SCHEMA = {
    "additionalProperties": {
        "type": "string"
    },
    "name": "image",
    "links": [
        {
            "href": "{self}",
            "rel": "self"
        },
        {
            "href": "{file}",
            "rel": "enclosure"
        },
        {
            "href": "{schema}",
            "rel": "describedby"
        }
    ],
    "properties": {
        "container_format": {
            "enum": [
                "ami",
                "ari",
                "aki",
                "bare",
                "ovf",
                "ova"
            ],
            "type": "string",
            "description": "Format of the container"
        },
        "min_ram": {
            "type": "integer",
            "description": "Amount of ram (in MB) required to boot image."
        },
        "ramdisk_id": {
            "pattern": ("^([0-9a-fA-F]){8}-([0-9a-fA-F]){4}"
                        "-([0-9a-fA-F]){4}-([0-9a-fA-F]){4}"
                        "-([0-9a-fA-F]){12}$"),
            "type": "string",
            "description": ("ID of image stored in Glance that should be "
                            "used as the ramdisk when booting an AMI-style "
                            "image.")
        },
        "locations": {
            "items": {
                "required": [
                    "url",
                    "metadata"
                ],
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "maxLength": 255
                    },
                    "metadata": {
                        "type": "object"
                    }
                }
            },
            "type": "array",
            "description": ("A set of URLs to access the image "
                            "file kept in external store")
        },
        "file": {
            "type": "string",
            "description": "(READ-ONLY)"
        },
        "owner": {
            "type": "string",
            "description": "Owner of the image",
            "maxLength": 255
        },
        "id": {
            "pattern": ("^([0-9a-fA-F]){8}-([0-9a-fA-F]){4}"
                        "-([0-9a-fA-F]){4}-([0-9a-fA-F]){4}"
                        "-([0-9a-fA-F]){12}$"),
            "type": "string",
            "description": "An identifier for the image"
        },
        "size": {
            "type": "integer",
            "description": "Size of image file in bytes (READ-ONLY)"
        },
        "os_distro": {
            "type": "string",
            "description": ("Common name of operating system distribution "
                            "as specified in %s" % _doc_url)
        },
        "self": {
            "type": "string",
            "description": "(READ-ONLY)"
        },
        "disk_format": {
            "enum": [
                "ami",
                "ari",
                "aki",
                "vhd",
                "vmdk",
                "raw",
                "qcow2",
                "vdi",
                "iso"
            ],
            "type": "string",
            "description": "Format of the disk"
        },
        "os_version": {
            "type": "string",
            "description": ("Operating system version as "
                            "specified by the distributor")
        },
        "direct_url": {
            "type": "string",
            "description": ("URL to access the image file kept in "
                            "external store (READ-ONLY)")
        },
        "schema": {
            "type": "string",
            "description": "(READ-ONLY)"
        },
        "status": {
            "enum": [
                "queued",
                "saving",
                "active",
                "killed",
                "deleted",
                "pending_delete"
            ],
            "type": "string",
            "description": "Status of the image (READ-ONLY)"
        },
        "tags": {
            "items": {
                "type": "string",
                "maxLength": 255
            },
            "type": "array",
            "description": "List of strings related to the image"
        },
        "kernel_id": {
            "pattern": ("^([0-9a-fA-F]){8}-([0-9a-fA-F]){4}-"
                        "([0-9a-fA-F]){4}-([0-9a-fA-F]){4}-"
                        "([0-9a-fA-F]){12}$"),
            "type": "string",
            "description": ("ID of image stored in Glance that should be "
                            "used as the kernel when booting an AMI-style "
                            "image.")
        },
        "visibility": {
            "enum": [
                "public",
                "private"
            ],
            "type": "string",
            "description": "Scope of image accessibility"
        },
        "updated_at": {
            "type": "string",
            "description": ("Date and time of the last "
                            "image modification (READ-ONLY)")
        },
        "min_disk": {
            "type": "integer",
            "description": ("Amount of disk space (in GB) "
                            "required to boot image.")
        },
        "virtual_size": {
            "type": "integer",
            "description": "Virtual size of image in bytes (READ-ONLY)"
        },
        "instance_uuid": {
            "type": "string",
            "description": "ID of instance used to create this image."
        },
        "name": {
            "type": "string",
            "description": "Descriptive name for the image",
            "maxLength": 255
        },
        "checksum": {
            "type": "string",
            "description": "md5 hash of image contents. (READ-ONLY)",
            "maxLength": 32
        },
        "created_at": {
            "type": "string",
            "description": "Date and time of image registration (READ-ONLY)"
        },
        "protected": {
            "type": "boolean",
            "description": "If true, image will not be deletable."
        },
        "architecture": {
            "type": "string",
            "description": ("Operating system architecture as specified "
                            "in %s" % _doc_url)
        }
    }
}
