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

import ConfigParser
import os

from tempest_lib.cli import base


class ClientTestBase(base.ClientTestBase):
    """
    This is a first pass at a simple read only python-glanceclient test. This
    only exercises client commands that are read only.

    This should test commands:
    * as a regular user
    * as an admin user
    * with and without optional parameters
    * initially just check return codes, and later test command outputs

    """

    def __init__(self, *args, **kwargs):
        super(ClientTestBase, self).__init__(*args, **kwargs)

        # Collecting of credentials:
        #
        # Support the existence of a functional_creds.conf for
        # testing. This makes it possible to use a config file.
        self.username = os.environ.get('OS_USERNAME')
        self.password = os.environ.get('OS_PASSWORD')
        self.tenant_name = os.environ.get('OS_TENANT_NAME')
        self.uri = os.environ.get('OS_AUTH_URL')
        config = ConfigParser.RawConfigParser()
        if config.read('functional_creds.conf'):
            # the OR pattern means the environment is preferred for
            # override
            self.username = self.username or config.get('admin', 'user')
            self.password = self.password or config.get('admin', 'pass')
            self.tenant_name = self.tenant_name or config.get('admin',
                                                              'tenant')
            self.uri = self.uri or config.get('auth', 'uri')

    def _get_clients(self):
        cli_dir = os.environ.get(
            'OS_GLANCECLIENT_EXEC_DIR',
            os.path.join(os.path.abspath('.'), '.tox/functional/bin'))

        return base.CLIClient(
            username=self.username,
            password=self.password,
            tenant_name=self.tenant_name,
            uri=self.uri,
            cli_dir=cli_dir)

    def glance(self, *args, **kwargs):
        return self.clients.glance(*args,
                                   **kwargs)
