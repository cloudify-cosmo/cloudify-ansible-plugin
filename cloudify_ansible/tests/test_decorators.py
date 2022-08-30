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
from mock import Mock, patch, mock_open
from cloudify_ansible import (
    constants,
    ansible_playbook_node
)

from cloudify.mocks import MockCloudifyContext
from cloudify.state import current_ctx

from cloudify_ansible_sdk._compat import PY2
from cloudify_ansible_sdk.tests import AnsibleTestBase

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
    'resource_config': {},
    'workspace': '/path/to/workdir'
}
RELS = []
OP_CTX = {
    'retry_number': 0,
    'name': 'cloudify.interfaces.lifecycle.'
}


class TestDecorator(AnsibleTestBase):

    def tearDown(self):
        current_ctx.clear()
        super(TestDecorator, self).tearDown()

    def _get_ctx(self):
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
            source=ctx,
            target=compute_ctx)
        return relationship_ctx

    @patch('cloudify_common_sdk.utils.get_deployment_dir')
    @patch('cloudify_ansible.create_playbook_workspace')
    def test_ansible_playbook_node(self, *_):
        # without remerge
        relationship_ctx = self._get_ctx()
        current_ctx.set(relationship_ctx)

        if PY2:
            builtins_open = '__builtin__.open'
        else:
            builtins_open = 'builtins.open'
        func = Mock()
        with patch(
            "cloudify_ansible.handle_site_yaml",
            Mock(return_value="Check")
        ):
            fake_file = mock_open()
            with patch(
                builtins_open, fake_file
            ):
                with patch('cloudify_ansible.create_playbook_venv'):
                    ansible_playbook_node(func)(
                        playbook_path=self.playbook_path)
            fake_file.assert_called_with("hosts", "w")
        func.assert_called_with(
            {
                'playbook_path': 'Check',
                'sources': 'hosts',
                'verbosity': 2,
                'logger': relationship_ctx.logger,
                'additional_args': ''
            }, {
                constants.OPTION_HOST_CHECKING: "False",
                constants.OPTION_TASK_FAILED_ATTRIBUTE: "False",
                constants.OPTION_STDOUT_FORMAT: "json"
            },
            relationship_ctx)

    @patch('cloudify_common_sdk.utils.get_deployment_dir')
    @patch('cloudify_ansible.create_playbook_workspace')
    def test_ansible_playbook_node_remerge(self, *_):
        # remerge
        relationship_ctx = self._get_ctx()
        current_ctx.set(relationship_ctx)

        if PY2:
            builtins_open = '__builtin__.open'
        else:
            builtins_open = 'builtins.open'
        func = Mock()
        with patch(
            "cloudify_ansible.handle_site_yaml",
            Mock(return_value="Check")
        ):
            fake_file = mock_open()
            with patch(
                builtins_open, fake_file
            ):
                with patch('cloudify_ansible.create_playbook_venv'):
                    ansible_playbook_node(func)(
                        playbook_path=self.playbook_path,
                        group_name="name_of_group",
                        remerge_sources=True)
            fake_file.assert_called_with("hosts", "w")
        func.assert_called_with(
            {
                'playbook_path': 'Check',
                'sources': 'hosts',
                'verbosity': 2,
                'logger': relationship_ctx.logger,
                'additional_args': '',
                'group_name': "name_of_group"
            }, {
                constants.OPTION_HOST_CHECKING: "False",
                constants.OPTION_TASK_FAILED_ATTRIBUTE: "False",
                constants.OPTION_STDOUT_FORMAT: "json"
            },
            relationship_ctx)
