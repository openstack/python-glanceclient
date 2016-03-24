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
    "definitions": {
        "positiveInteger": {
            "minimum": 0,
            "type": "integer"
        },
        "positiveIntegerDefault0": {
            "allOf": [
                {"$ref": "#/definitions/positiveInteger"},
                {"default": 0}
            ]
        },
        "stringArray": {
            "type": "array",
            "items": {"type": "string"},
            "uniqueItems": True
        },
        "property": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "required": ["title", "type"],
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "title": {
                        "type": "string"
                    },
                    "description": {
                        "type": "string"
                    },
                    "operators": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },
                    "type": {
                        "type": "string",
                        "enum": [
                            "array",
                            "boolean",
                            "integer",
                            "number",
                            "object",
                            "string",
                            None
                        ]
                    },
                    "required": {
                        "$ref": "#/definitions/stringArray"
                    },
                    "minimum": {
                        "type": "number"
                    },
                    "maximum": {
                        "type": "number"
                    },
                    "maxLength": {
                        "$ref": "#/definitions/positiveInteger"
                    },
                    "minLength": {
                        "$ref": "#/definitions/positiveIntegerDefault0"
                    },
                    "pattern": {
                        "type": "string",
                        "format": "regex"
                    },
                    "enum": {
                        "type": "array"
                    },
                    "readonly": {
                        "type": "boolean"
                    },
                    "default": {},
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": [
                                    "array",
                                    "boolean",
                                    "integer",
                                    "number",
                                    "object",
                                    "string",
                                    None
                                ]
                            },
                            "enum": {
                                "type": "array"
                            }
                        }
                    },
                    "maxItems": {
                        "$ref": "#/definitions/positiveInteger"
                    },
                    "minItems": {
                        "$ref": "#/definitions/positiveIntegerDefault0"
                    },
                    "uniqueItems": {
                        "type": "boolean",
                        "default": False
                    },
                    "additionalItems": {
                        "type": "boolean"
                    },
                }
            }
        }
    },
    "required": ["namespace"],
    "name": "namespace",
    "properties": {
        "namespace": {
            "type": "string",
            "description": "The unique namespace text.",
            "maxLength": 80
        },
        "display_name": {
            "type": "string",
            "description": "The user friendly name for the namespace. Used by "
                           "UI if available.",
            "maxLength": 80
        },
        "description": {
            "type": "string",
            "description": "Provides a user friendly description of the "
                           "namespace.",
            "maxLength": 500
        },
        "visibility": {
            "enum": [
                "public",
                "private"
            ],
            "type": "string",
            "description": "Scope of namespace accessibility."
        },
        "protected": {
            "type": "boolean",
            "description": "If true, namespace will not be deletable."
        },
        "owner": {
            "type": "string",
            "description": "Owner of the namespace.",
            "maxLength": 255
        },
        "created_at": {
            "type": "string",
            "readOnly": True,
            "description": "Date and time of namespace creation.",
            "format": "date-time"
        },
        "updated_at": {
            "type": "string",
            "readOnly": True,
            "description": "Date and time of the last namespace modification.",
            "format": "date-time"
        },
        "schema": {
            "readOnly": True,
            "type": "string"
        },
        "self": {
            "readOnly": True,
            "type": "string"
        },
        "resource_type_associations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    },
                    "prefix": {
                        "type": "string"
                    },
                    "properties_target": {
                        "type": "string"
                    }
                }
            }
        },
        "properties": {
            "$ref": "#/definitions/property"
        },
        "objects": {
            "items": {
                "type": "object",
                "properties": {
                    "required": {
                        "$ref": "#/definitions/stringArray"
                    },
                    "description": {
                        "type": "string"
                    },
                    "name": {
                        "type": "string"
                    },
                    "properties": {
                        "$ref": "#/definitions/property"
                    }
                }
            },
            "type": "array"
        },
        "tags": {
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                    }
                }
            },
            "type": "array"
        },
    }
}
