# Copyright (c) 2019 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from mock import patch
import unittest

from cloudify.exceptions import NonRecoverableError
from cloudify.mocks import MockCloudifyContext
from cloudify_ansible.tasks import run

NODE_PROPS = {
    'resource_id': None,
    'use_external_resource': False,
    'resource_config': {}
}
RUNTIME_PROPS = {
    'external_id': None,
    'resource_config': {}
}
RELS = []
OP_CTX = {
    'retry_number': 0,
    'name': 'cloudify.interfaces.lifecycle.'
}

ctx = MockCloudifyContext(
    node_name='mock_node_name',
    node_id='node_id',
    deployment_id='mock_deployment_id',
    properties=NODE_PROPS,
    runtime_properties=RUNTIME_PROPS,
    relationships=RELS,
    operation=OP_CTX
)

ctx.node.type_hierarchy = ['cloudify.nodes.Root']


class AnsibleTasksTest(unittest.TestCase):

    _CWD = os.path.abspath(os.path.dirname(__file__))

    def setUp(self):
        super(AnsibleTasksTest, self).setUp()

    def tearDown(self):
        super(AnsibleTasksTest, self).tearDown()

    @property
    def cwd(self):
        path_components = self._CWD.split('/')[1:-2]
        _cwd = '/'.join(path_components)
        _cwd = '/{0}'.format(_cwd)
        return _cwd

    @property
    def playbook_path(self):
        return os.path.join(
            self.cwd,
            'examples/ansible-examples/lamp_simple/site.yml'
        )

    @property
    def hosts_path(self):
        return os.path.join(
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

    @patch('ansible.executor.playbook_executor.PlaybookExecutor.run')
    def test_ansible_playbook(self, foo):
        instance = foo.return_value
        instance.method.return_value = self.mock_runner_return
        run(
            self.playbook_path,
            self.hosts_path,
            ctx=ctx)

    @patch('ansible.executor.playbook_executor.PlaybookExecutor.run')
    def test_ansible_playbook_raises(self, foo):
        instance = foo.return_value
        instance.method.return_value = self.mock_runner_return
        with self.assertRaises(NonRecoverableError) as e:
            run(
                self.playbook_path,
                self.hosts_path,
                inventory_config=['host1', 'host2'],
                ctx=ctx)
            self.assertIn('inventory_config must be a dictionary.',
                          e.message)

    @unittest.skipUnless(
        os.environ.get('TEST_ZPLAYS', False),
        reason='This test requires you to run "vagrant up". '
               'And export TEST_ZPLAYS=true')
    def test_zplays(self):
        run(
            self.playbook_path,
            self.hosts_path,
            ctx=ctx)
