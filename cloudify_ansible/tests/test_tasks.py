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

from os import environ, curdir, path
from mock import patch
import shutil
from tempfile import mkdtemp
import unittest

from cloudify.exceptions import NonRecoverableError
from cloudify.mocks import MockCloudifyContext
from cloudify.state import current_ctx

from cloudify_ansible_sdk.tests import AnsibleTestBase, mock_sources_dict

from cloudify_ansible.tasks import run, ansible_requires_host
from cloudify_ansible.utils import handle_file_path, handle_key_data

NODE_PROPS = {
    'resource_id': None,
    'use_external_resource': False,
    'resource_config': {}
}
COMPUTE_NODE_PROPS = {
    'resource_id': None,
    'use_external_resource': False,
    'resource_config': {},
    'agent_config': {}
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
compute_ctx = MockCloudifyContext(
    node_name='mock_compute_node_name',
    node_id='compute_node_id',
    deployment_id='mock_deployment_id',
    properties=COMPUTE_NODE_PROPS,
    runtime_properties=RUNTIME_PROPS,
    relationships=RELS,
    operation=OP_CTX
)
compute_ctx.node.type_hierarchy = \
    ['cloudify.nodes.Root', 'cloudify.nodes.Compute']
relationship_ctx = MockCloudifyContext(
    deployment_id='mock_deployment_id',
    properties=NODE_PROPS,
    source=ctx,
    target=compute_ctx,
    runtime_properties=RUNTIME_PROPS)

# Fix the mock ctx.
setattr(ctx, '_local', True)


class TestPluginTasks(AnsibleTestBase):

    def test_handle_key_data(self):

        def _finditem(obj, key):
            # Stolen https://stackoverflow.com/questions/14962485/
            # finding-a-key-recursively-in-a-dictionary
            if key in obj:
                return obj[key]
            for k, v in obj.items():
                if isinstance(v, dict):
                    return _finditem(v, key)  # added return statement

        deleteme = mkdtemp()
        key_data = handle_key_data(mock_sources_dict, deleteme)
        output = _finditem(
            key_data['all']['children'],
            'ansible_ssh_private_key_file')
        self.assertTrue(deleteme, path.dirname(output))
        shutil.rmtree(deleteme)

    def test_handle_file_path(self):
        setattr(ctx, '_local', False)
        with self.assertRaises(NonRecoverableError):
            self.assertEquals(
                '/opt/manager/resources/blueprints/None/None/foo',
                handle_file_path('foo', ctx))
        setattr(ctx, '_local', True)
        self.assertEquals(
            curdir,
            handle_file_path(curdir, ctx))

    @patch('ansible.executor.playbook_executor.PlaybookExecutor.run')
    def test_ansible_playbook(self, foo):
        instance = foo.return_value
        instance.method.return_value = self.mock_runner_return
        run(
            self.playbook_path,
            self.hosts_path,
            ctx=ctx)

    @patch('ansible.executor.playbook_executor.PlaybookExecutor.run')
    def test_ansible_playbook_with_dict_sources(self, foo):
        instance = foo.return_value
        instance.method.return_value = self.mock_runner_return
        run(
            self.playbook_path,
            mock_sources_dict,
            ctx=ctx)

    @unittest.skipUnless(
        environ.get('TEST_ZPLAYS', False),
        reason='This test requires you to run "vagrant up". '
               'And export TEST_ZPLAYS=true')
    def test_zplays(self):
        run(
            self.playbook_path,
            self.hosts_path,
            ctx=ctx)

    def test_ansible_requires_host(self):
        current_ctx.set(relationship_ctx)
        ansible_requires_host(ctx=relationship_ctx)
