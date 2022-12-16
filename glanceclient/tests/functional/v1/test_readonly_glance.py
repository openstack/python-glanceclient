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

import re

from tempest.lib import exceptions

from glanceclient.tests.functional import base


class SimpleReadOnlyGlanceClientTest(base.ClientTestBase):

    """Read only functional python-glanceclient tests.

    This only exercises client commands that are read only.
    """

    def test_list_v1(self):
        out = self.glance('--os-image-api-version 1 image-list')
        endpoints = self.parser.listing(out)
        self.assertTableStruct(endpoints, [
            'ID', 'Name', 'Disk Format', 'Container Format',
            'Size', 'Status'])

    def test_fake_action(self):
        self.assertRaises(exceptions.CommandFailed,
                          self.glance,
                          'this-does-not-exist')

    def test_member_list_v1(self):
        tenant_name = '--tenant-id %s' % self.creds['project_name']
        out = self.glance('--os-image-api-version 1 member-list',
                          params=tenant_name)
        endpoints = self.parser.listing(out)
        self.assertTableStruct(endpoints,
                               ['Image ID', 'Member ID', 'Can Share'])

    def test_help(self):
        help_text = self.glance('--os-image-api-version 1 help')
        lines = help_text.split('\n')
        self.assertFirstLineStartsWith(lines, 'usage: glance')

        commands = []
        cmds_start = lines.index('Positional arguments:')
        try:
            # Starting in Python 3.10, argparse displays options in the
            # "Options:" section...
            cmds_end = lines.index('Options:')
        except ValueError:
            # ... but before Python 3.10, options were displayed in the
            # "Optional arguments:" section.
            cmds_end = lines.index('Optional arguments:')
        command_pattern = re.compile(r'^ {4}([a-z0-9\-\_]+)')
        for line in lines[cmds_start:cmds_end]:
            match = command_pattern.match(line)
            if match:
                commands.append(match.group(1))
        commands = set(commands)
        wanted_commands = {'bash-completion', 'help',
                           'image-create', 'image-delete',
                           'image-download', 'image-list',
                           'image-show', 'image-update',
                           'member-create', 'member-delete',
                           'member-list'}
        self.assertEqual(commands, wanted_commands)

    def test_version(self):
        self.glance('', flags='--version')

    def test_debug_list(self):
        self.glance('--os-image-api-version 1 image-list', flags='--debug')
