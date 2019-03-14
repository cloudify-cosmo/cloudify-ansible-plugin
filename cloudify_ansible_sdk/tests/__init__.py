# Copyright (c) 2019 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from os import path
import unittest

key_file = '.vagrant/machines/{0}/virtualbox/private_key'
mock_sources_dict = {
    'all': {
        'hosts': {},
        'children': {
            'webservers': {
                'hosts': {
                    'web': {
                        'ansible_host': '11.0.0.7',
                        'ansible_user': 'vagrant',
                        'ansible_ssh_private_key_file': key_file.format('web'),
                        'ansible_become': True,
                        'ansible_ssh_common_args':
                            '-o StrictHostKeyChecking=no'
                    }
                }
            }, 'dbservers': {
                'hosts': {
                    'db': {
                        'ansible_host': '11.0.0.8',
                        'ansible_user': 'vagrant',
                        'ansible_ssh_private_key_file': key_file.format('db'),
                        'ansible_become': True,
                        'ansible_ssh_common_args':
                            '-o StrictHostKeyChecking=no'
                    },
                }
            }
        }
    }
}


class AnsibleTestBase(unittest.TestCase):

    def setUp(self):
        super(AnsibleTestBase, self).setUp()

    def tearDown(self):
        super(AnsibleTestBase, self).tearDown()

    @property
    def cwd(self):
        return '/{0}'.format(
            '/'.join(
                path.abspath(
                    path.dirname(__file__)
                ).split('/')[1:-2]
            )
        )

    @property
    def playbook_path(self):
        return path.join(
            self.cwd,
            'examples/ansible-examples/lamp_simple/site.yml'
        )

    @property
    def hosts_path(self):
        return path.join(
            self.cwd,
            'examples/ansible-examples/lamp_simple/hosts'
        )

    @property
    def mock_runner_return(self):
        return {
            'skipped': {},
            'ok': {},
            'changed': {},
            'custom': {},
            'dark': {},
            'processed': {},
            'failures': {}
        }
