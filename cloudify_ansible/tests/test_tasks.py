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

import shutil
from mock import patch
from unittest import skipUnless
from os import environ, curdir, path, remove
from tempfile import mkdtemp, NamedTemporaryFile


from cloudify.exceptions import (NonRecoverableError,
                                 OperationRetry,
                                 HttpException)
from cloudify.mocks import MockNodeInstanceContext, MockCloudifyContext
from cloudify.state import current_ctx
from script_runner.tasks import ProcessException


from cloudify_ansible_sdk.tests import AnsibleTestBase, mock_sources_dict
import cloudify_ansible_sdk

from cloudify_ansible.constants import WORKSPACE
from cloudify_ansible.tasks import (
    run, ansible_requires_host, ansible_remove_host, cleanup)
from cloudify_ansible.utils import (
    handle_file_path, handle_key_data, handle_source_from_string)

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
    'playbook_venv': '/tmp/path/to/venv'
}
RELS = []
OP_CTX = {
    'retry_number': 0,
    'name': 'cloudify.interfaces.lifecycle.'
}

work_dir = path.abspath(environ.get('CIRCLE_WORKING_DIRECTORY', curdir))
blueprint_resources = {
    path.join(
        work_dir,
        'examples/ansible-examples/'
        'lamp_simple/hosts'): NamedTemporaryFile(delete=False).name
}


class MockNodeInstanceCtx(MockNodeInstanceContext):

    def refresh(self, *_, **__):
        pass

    def update(self, *_, **__):
        pass


class MockC1oudifyContext(MockCloudifyContext):

    def __init__(self, *_, **kwargs):
        super().__init__(*_, **kwargs)
        self._instance = MockNodeInstanceCtx(
            id=kwargs.get('node_id'),
            runtime_properties=self._runtime_properties,
            relationships=kwargs.get('relationships'),
            index=kwargs.get('index'))


ctx = MockC1oudifyContext(
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
relationship_ctx = MockC1oudifyContext(
    deployment_id='mock_deployment_id',
    source=ctx,
    target=compute_ctx)
ctx._resources = blueprint_resources

# Fix the mock ctx.
setattr(ctx, '_local', True)

FAKE_INVENTORY = \
    """mail.example.com

[webservers]
foo.example.com
bar.example.com

[dbservers]
one.example.com
two.example.com
three.example.com
"""


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

    @patch('cloudify_ansible.utils.get_blueprint_dir')
    @patch('cloudify_common_sdk.utils.get_blueprint_dir')
    def test_handle_file_path(self, _, mock_bp_dir, *__):
        with patch('cloudify_ansible.utils.get_rest_client'):
            setattr(ctx, '_local', False)
            mock_bp_dir.return_value = \
                '/opt/manager/resources/blueprints/None/None'
            with patch('os.path.exists', return_value=False):
                with self.assertRaises(NonRecoverableError):
                    self.assertEquals(
                        '/opt/manager/resources/blueprints/None/None/foo',
                        handle_file_path('foo', [], ctx))
            setattr(ctx, '_local', True)
            self.assertEquals(
                curdir,
                handle_file_path(curdir, [], ctx))

    @patch('cloudify_ansible.utils._get_collections_location')
    @patch('cloudify_ansible.utils.get_deployment_dir')
    @patch.object(cloudify_ansible_sdk.AnsiblePlaybookFromFile, 'execute')
    @patch('cloudify_common_sdk.utils.get_deployment_dir')
    @patch('cloudify_common_sdk.utils.get_node_instance_dir')
    def test_ansible_playbook(self, foo, mock_dir, *_):
        mock_dir.return_value = mkdtemp()
        _[-1].return_value = mkdtemp()
        _[-2].return_value = mkdtemp()
        with patch('cloudify_ansible.create_playbook_venv'):
            foo.return_value = ('output', 'error', 0)
            current_ctx.set(ctx)
            run(
                self.playbook_path,
                self.hosts_path,
                ctx=ctx)
        shutil.rmtree(mock_dir())

    @patch('cloudify_ansible.utils._get_collections_location')
    @patch('cloudify_ansible.utils.get_deployment_dir')
    @patch('cloudify_common_sdk.utils.get_deployment_dir')
    @patch.object(cloudify_ansible_sdk.AnsiblePlaybookFromFile, 'execute')
    def test_ansible_playbook_failed_sdk(self, foo, mock_dir, mock_dir2, *_):
        foo.side_effect = cloudify_ansible_sdk.CloudifyAnsibleSDKError(
            "We are failed!")
        current_ctx.set(ctx)
        _[-1].return_value = mkdtemp()
        mock_dir.return_value = mkdtemp()
        mock_dir2.return_value = mkdtemp()
        ctx.instance.runtime_properties[WORKSPACE] = mock_dir.return_value
        with patch('cloudify_ansible.create_playbook_venv'):
            with self.assertRaisesRegexp(NonRecoverableError,
                                         "We are failed!"):
                run(
                    self.playbook_path,
                    self.hosts_path,
                    ctx=ctx)
        shutil.rmtree(mock_dir())

    @patch('cloudify_ansible.utils._get_collections_location')
    @patch('cloudify_ansible.utils.get_deployment_dir')
    @patch('cloudify_common_sdk.utils.get_deployment_dir')
    @patch.object(cloudify_ansible_sdk.AnsiblePlaybookFromFile, 'execute')
    def test_ansible_playbook_failed(self, foo, mock_dir, mock_dir2, *_):
        _[-1].return_value = mkdtemp()
        mock_dir.return_value = mkdtemp()
        mock_dir2.return_value = mkdtemp()
        foo.side_effect = ProcessException('Unable to run command', -1)
        current_ctx.set(ctx)
        ctx.instance.runtime_properties[WORKSPACE] = mock_dir.return_value
        with patch('cloudify_ansible.create_playbook_venv'):
            with self.assertRaises(NonRecoverableError):
                run(
                    self.playbook_path,
                    self.hosts_path,
                    ctx=ctx)
        shutil.rmtree(mock_dir())

    @patch('cloudify_ansible.utils._get_collections_location')
    @patch('cloudify_ansible.utils.get_deployment_dir')
    @patch('cloudify_common_sdk.utils.get_deployment_dir')
    @patch.object(cloudify_ansible_sdk.AnsiblePlaybookFromFile, 'execute')
    def test_ansible_playbook_retry(self, foo, mock_dir, mock_dir2, *_):
        _[-1].return_value = mkdtemp()
        mock_dir.return_value = mkdtemp()
        mock_dir2.return_value = mkdtemp()
        foo.side_effect = ProcessException(
            'One or more hosts are unreachable.', 4)
        current_ctx.set(ctx)
        ctx.instance.runtime_properties[WORKSPACE] = mock_dir.return_value
        with patch('cloudify_ansible.create_playbook_venv'):
            with self.assertRaises(OperationRetry):
                run(
                    self.playbook_path,
                    self.hosts_path,
                    number_of_attempts=self.number_of_attempts,
                    ctx=ctx)
        shutil.rmtree(mock_dir())

    @patch('cloudify_ansible.utils._get_collections_location')
    @patch('cloudify_ansible.utils.get_deployment_dir')
    @patch('cloudify_common_sdk.utils.get_deployment_dir')
    @patch.object(cloudify_ansible_sdk.AnsiblePlaybookFromFile, 'execute')
    def test_ansible_playbook_retry_not_allowed(self,
                                                foo,
                                                mock_dir,
                                                mock_dir2,
                                                *_):
        _[-1].return_value = mkdtemp()
        mock_dir.return_value = mkdtemp()
        mock_dir2.return_value = mkdtemp()
        foo.side_effect = ProcessException(
            'One or more hosts are unreachable.', 4)
        current_ctx.set(ctx)
        ctx.instance.runtime_properties[WORKSPACE] = mock_dir.return_value
        with patch('cloudify_ansible.create_playbook_venv'):
            with self.assertRaises(NonRecoverableError):
                run(
                    self.playbook_path,
                    self.hosts_path,
                    number_of_attempts=1,
                    ctx=ctx)
        shutil.rmtree(mock_dir())

    @patch('cloudify_ansible.utils._get_collections_location')
    @patch('cloudify_ansible.utils.get_deployment_dir')
    @patch('cloudify_common_sdk.utils.get_deployment_dir')
    @patch.object(cloudify_ansible_sdk.AnsiblePlaybookFromFile, 'execute')
    def test_ansible_playbook_with_dict_sources(self,
                                                foo,
                                                mock_dir,
                                                mock_dir2,
                                                *_):
        _[-1].return_value = mkdtemp()
        mock_dir.return_value = mkdtemp()
        mock_dir2.return_value = mkdtemp()
        foo.side_effect = cloudify_ansible_sdk.CloudifyAnsibleSDKError(
            "We are failed!"
        )
        current_ctx.set(ctx)
        ctx.instance.runtime_properties[WORKSPACE] = mock_dir.return_value
        with patch('cloudify_ansible.create_playbook_venv'):
            with self.assertRaises(NonRecoverableError):
                run(
                    self.playbook_path,
                    mock_sources_dict,
                    ctx=ctx)
        shutil.rmtree(mock_dir())

    @skipUnless(
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

    def test_ansible_remove_host(self):
        current_ctx.set(relationship_ctx)
        ansible_remove_host(ctx=relationship_ctx)

    def test_cleanup(self):
        current_ctx.set(ctx)
        cleanup(ctx=ctx)

    def test_handle_source_from_string(self):
        # Mock the download resource when passing fake inventory
        with patch('cloudify.mocks.MockCloudifyContext.download_resource') \
                as mock_download:
            mock_download.side_effect = HttpException(FAKE_INVENTORY,
                                                      '404',
                                                      'File not found')
            f1 = NamedTemporaryFile(delete=False)
            self.addCleanup(remove, f1.name)
            result = handle_source_from_string(FAKE_INVENTORY, ctx, f1.name)
            self.assertTrue(path.exists(result))
            self.assertTrue(FAKE_INVENTORY in open(result).read())

        f2 = NamedTemporaryFile(delete=False)
        self.addCleanup(remove, f2.name)
        result = handle_source_from_string(f2.name, ctx, f1.name)
        self.assertTrue(path.exists(result))
        self.assertRaises(RuntimeError,
                          handle_source_from_string,
                          'bad/file/path',
                          ctx,
                          f1.name)
