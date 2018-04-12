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

import glanceclient
from keystoneauth1 import loading
from keystoneauth1 import session
import os
import os_client_config
from tempest.lib.cli import base


def credentials(cloud='devstack-admin'):
    """Retrieves credentials to run functional tests

    Credentials are either read via os-client-config from the environment
    or from a config file ('clouds.yaml'). Environment variables override
    those from the config file.

    devstack produces a clouds.yaml with two named clouds - one named
    'devstack' which has user privs and one named 'devstack-admin' which
    has admin privs. This function will default to getting the devstack-admin
    cloud as that is the current expected behavior.
    """

    return os_client_config.OpenStackConfig().get_one_cloud(cloud=cloud)


class ClientTestBase(base.ClientTestBase):
    """This is a first pass at a simple read only python-glanceclient test.

    This only exercises client commands that are read only.
    This should test commands:
    * as a regular user
    * as an admin user
    * with and without optional parameters
    * initially just check return codes, and later test command outputs

    """

    def _get_clients(self):
        self.creds = credentials().get_auth_args()
        venv_name = os.environ.get('OS_TESTENV_NAME', 'functional')
        cli_dir = os.environ.get(
            'OS_GLANCECLIENT_EXEC_DIR',
            os.path.join(os.path.abspath('.'), '.tox/%s/bin' % venv_name))

        return base.CLIClient(
            username=self.creds['username'],
            password=self.creds['password'],
            tenant_name=self.creds['project_name'],
            user_domain_id=self.creds['user_domain_id'],
            project_domain_id=self.creds['project_domain_id'],
            uri=self.creds['auth_url'],
            cli_dir=cli_dir)

    def glance(self, *args, **kwargs):
        return self.clients.glance(*args,
                                   **kwargs)

    def glance_pyclient(self):
        ks_creds = dict(
            auth_url=self.creds["auth_url"],
            username=self.creds["username"],
            password=self.creds["password"],
            project_name=self.creds["project_name"],
            user_domain_id=self.creds["user_domain_id"],
            project_domain_id=self.creds["project_domain_id"])
        keystoneclient = self.Keystone(**ks_creds)
        return self.Glance(keystoneclient)

    class Keystone(object):
        def __init__(self, **kwargs):
            loader = loading.get_plugin_loader("password")
            auth = loader.load_from_options(**kwargs)
            self.session = session.Session(auth=auth)

    class Glance(object):
        def __init__(self, keystone, version="2"):
            self.glance = glanceclient.Client(
                version,
                session=keystone.session)

        def find(self, image_name):
            for image in self.glance.images.list():
                if image.name == image_name:
                    return image
            return None
