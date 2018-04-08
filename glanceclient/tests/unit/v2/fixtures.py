# Copyright (c) 2015 OpenStack Foundation
# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
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

UUID = "3fc2ba62-9a02-433e-b565-d493ffc69034"

image_list_fixture = {
    "images": [
        {
            "checksum": "9cb02fe7fcac26f8a25d6db3109063ae",
            "container_format": "bare",
            "created_at": "2015-07-23T16:58:50.000000",
            "deleted": "false",
            "deleted_at": "null",
            "disk_format": "raw",
            "id": UUID,
            "is_public": "false",
            "min_disk": 0,
            "min_ram": 0,
            "name": "test",
            "owner": "3447cea05d6947658d73791ed9e0ed9f",
            "properties": {
                "kernel_id": 1234,
                "ramdisk_id": 5678
            },
            "protected": "false",
            "size": 145,
            "status": "active",
            "updated_at": "2015-07-23T16:58:51.000000",
            "virtual_size": "null"
        }
    ]
}

image_show_fixture = {
    "checksum": "9cb02fe7fcac26f8a25d6db3109063ae",
    "container_format": "bare",
    "created_at": "2015-07-24T12:18:13Z",
    "disk_format": "raw",
    "file": "/v2/images/%s/file" % UUID,
    "id": UUID,
    "kernel_id": "1234",
    "min_disk": 0,
    "min_ram": 0,
    "name": "img1",
    "owner": "411423405e10431fb9c47ac5b2446557",
    "protected": "false",
    "ramdisk_id": "5678",
    "schema": "/v2/schemas/image",
    "self": "/v2/images/%s" % UUID,
    "size": 145,
    "status": "active",
    "tags": [],
    "updated_at": "2015-07-24T12:18:13Z",
    "virtual_size": "null",
    "visibility": "shared"
}

image_create_fixture = {
    "checksum": "9cb02fe7fcac26f8a25d6db3109063ae",
    "container_format": "bare",
    "created_at": "2015-07-24T12:18:13Z",
    "disk_format": "raw",
    "file": "/v2/images/%s/file" % UUID,
    "id": UUID,
    "kernel_id": "af81fccd-b2e8-4232-886c-aa98dda22882",
    "min_disk": 0,
    "min_ram": 0,
    "name": "img1",
    "owner": "411423405e10431fb9c47ac5b2446557",
    "protected": False,
    "ramdisk_id": "fdb3f864-9458-4185-bd26-5d27fe6b6adf",
    "schema": "/v2/schemas/image",
    "self": "/v2/images/%s" % UUID,
    "size": 145,
    "status": "active",
    "tags": [],
    "updated_at": "2015-07-24T12:18:13Z",
    "virtual_size": 123,
    "visibility": "private"
}

schema_fixture = {
    "additionalProperties": {
        "type": "string"
    },
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
    "name": "image",
    "properties": {
        "architecture": {
            "description": "Operating system architecture as specified in "
                           "http://docs.openstack.org/user-guide/common"
                           "/cli_manage_images.html",
            "is_base": "false",
            "type": "string"
        },
        "checksum": {
            "readOnly": True,
            "description": "md5 hash of image contents.",
            "maxLength": 32,
            "type": [
                "null",
                "string"
            ]
        },
        "container_format": {
            "description": "Format of the container",
            "enum": [
                "null",
                "ami",
                "ari",
                "aki",
                "bare",
                "ovf",
                "ova",
                "docker"
            ],
            "type": [
                "null",
                "string"
            ]
        },
        "created_at": {
            "readOnly": True,
            "description": "Date and time of image registration",
            "type": "string"
        },
        "direct_url": {
            "readOnly": True,
            "description": "URL to access the image file kept in external "
                           "store",
            "type": "string"
        },
        "disk_format": {
            "description": "Format of the disk",
            "enum": [
                "null",
                "ami",
                "ari",
                "aki",
                "vhd",
                "vmdk",
                "raw",
                "qcow2",
                "vdi",
                "iso",
                "ploop"
            ],
            "type": [
                "null",
                "string"
            ]
        },
        "file": {
            "readOnly": True,
            "description": "An image file url",
            "type": "string"
        },
        "id": {
            "description": "An identifier for the image",
            "pattern": "^([0-9a-fA-F]){8}-([0-9a-fA-F]){4}-([0-9a-fA-F])"
                       "{4}-([0-9a-fA-F]){4}-([0-9a-fA-F]){12}$",
            "type": "string"
        },
        "instance_uuid": {
            "description": ("Metadata which can be used to record which "
                            "instance this image is associated with. "
                            "(Informational only, does not create an instance "
                            "snapshot.)"),
            "is_base": "false",
            "type": "string"
        },
        "kernel_id": {
            "description": "ID of image stored in Glance that should be used "
                           "as the kernel when booting an AMI-style image.",
            "is_base": "false",
            "pattern": "^([0-9a-fA-F]){8}-([0-9a-fA-F]){4}-([0-9a-fA-F])"
                       "{4}-([0-9a-fA-F]){4}-([0-9a-fA-F]){12}$",
            "type": [
                "null",
                "string"
            ]
        },
        "locations": {
            "description": "A set of URLs to access the image file kept "
                           "in external store",
            "items": {
                "properties": {
                    "metadata": {
                        "type": "object"
                    },
                    "url": {
                        "maxLength": 255,
                        "type": "string"
                    }
                },
                "required": [
                    "url",
                    "metadata"
                ],
                "type": "object"
            },
            "type": "array"
        },
        "min_disk": {
            "description": "Amount of disk space (in GB) required to "
                           "boot image.",
            "type": "integer"
        },
        "min_ram": {
            "description": "Amount of ram (in MB) required to boot image.",
            "type": "integer"
        },
        "name": {
            "description": "Descriptive name for the image",
            "maxLength": 255,
            "type": [
                "null",
                "string"
            ]
        },
        "os_distro": {
            "description": "Common name of operating system distribution as "
                           "specified in http://docs.openstack.org/trunk/"
                           "openstack-compute/admin/content/"
                           "adding-images.html",
            "is_base": "false",
            "type": "string"
        },
        "os_version": {
            "description": "Operating system version as specified "
                           "by the distributor",
            "is_base": "false",
            "type": "string"
        },
        "owner": {
            "description": "Owner of the image",
            "maxLength": 255,
            "type": [
                "null",
                "string"
            ]
        },
        "protected": {
            "description": "If true, image will not be deletable.",
            "type": "boolean"
        },
        "ramdisk_id": {
            "description": "ID of image stored in Glance that should be used "
                           "as the ramdisk when booting an AMI-style image.",
            "is_base": "false",
            "pattern": "^([0-9a-fA-F]){8}-([0-9a-fA-F]){4}-([0-9a-fA-F])"
                       "{4}-([0-9a-fA-F]){4}-([0-9a-fA-F]){12}$",
            "type": [
                "null",
                "string"
            ]
        },
        "schema": {
            "readOnly": True,
            "description": "An image schema url",
            "type": "string"
        },
        "self": {
            "readOnly": True,
            "description": "An image self url",
            "type": "string"
        },
        "size": {
            "readOnly": True,
            "description": "Size of image file in bytes",
            "type": [
                "null",
                "integer"
            ]
        },
        "status": {
            "readOnly": True,
            "description": "Status of the image",
            "enum": [
                "deactivated",
                "queued",
                "saving",
                "active",
                "killed",
                "deleted",
                "pending_delete",
                "uploading",
                "importing"
            ],
            "type": "string"
        },
        "tags": {
            "description": "List of strings related to the image",
            "items": {
                "maxLength": 255,
                "type": "string"
            },
            "type": "array"
        },
        "updated_at": {
            "readOnly": True,
            "description": "Date and time of the last image "
                           "modification",
            "type": "string"
        },
        "virtual_size": {
            "readOnly": True,
            "description": "Virtual size of image in bytes",
            "type": [
                "null",
                "integer"
            ]
        },
        "visibility": {
            "description": "Scope of image accessibility",
            "enum": [
                "public",
                "private",
                "community",
                "shared"
            ],
            "type": "string"
        }
    }
}

image_versions_fixture = {
    "versions": [
        {
            "id": "v2.3",
            "links": [
                {
                    "href": "http://localhost:9292/v2/",
                    "rel": "self"
                }
            ],
            "status": "CURRENT"
        },
        {
            "id": "v2.2",
            "links": [
                {
                    "href": "http://localhost:9292/v2/",
                    "rel": "self"
                }
            ],
            "status": "SUPPORTED"
        },
        {
            "id": "v2.1",
            "links": [
                {
                    "href": "http://localhost:9292/v2/",
                    "rel": "self"
                }
            ],
            "status": "SUPPORTED"
        },
        {
            "id": "v2.0",
            "links": [
                {
                    "href": "http://localhost:9292/v2/",
                    "rel": "self"
                }
            ],
            "status": "SUPPORTED"
        },
        {
            "id": "v1.1",
            "links": [
                {
                    "href": "http://localhost:9292/v1/",
                    "rel": "self"
                }
            ],
            "status": "SUPPORTED"
        },
        {
            "id": "v1.0",
            "links": [
                {
                    "href": "http://localhost:9292/v1/",
                    "rel": "self"
                }
            ],
            "status": "SUPPORTED"
        }
    ]
}
