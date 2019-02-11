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

from os import path, environ
from unittest import skipUnless

from cloudify.test_utils import workflow_test

from cloudify_ansible_sdk.tests import AnsibleTestBase, source_dict

# This just gives us a path to the setup.py directory.
_plugin_directory = \
    '/{0}'.format(
        '/'.join(
            path.abspath(path.dirname(__file__)).split('/')[1:-2]
        )
    )
_blueprint_path = \
   path.join(_plugin_directory, 'examples/blueprint.yaml')

_compute_blueprint_path = \
   path.join(_plugin_directory, 'examples/compute-blueprint.yaml')

web_private_key_path = \
    '.vagrant/machines/{0}/virtualbox/private_key'.format('web')
db_private_key_path = \
    '.vagrant/machines/{0}/virtualbox/private_key'.format('db')

with open(web_private_key_path, 'r') as infile:
    web_private_key = infile.read()

with open(db_private_key_path, 'r') as infile:
    db_private_key = infile.read()


class TestPlugin(AnsibleTestBase):

    @skipUnless(
        environ.get('TEST_ZPLAYS', False),
        reason='This test requires you to run "vagrant up". '
               'And export TEST_ZPLAYS=true')
    @workflow_test(_blueprint_path)
    def test_blueprint_defaults(self, cfy_local):
        cfy_local.execute('install', task_retries=0)
        self.assertIn(
            'result',
            cfy_local.storage.get_node_instances(
                )[0].runtime_properties.keys())

    @skipUnless(
        environ.get('TEST_ZPLAYS', False),
        reason='This test requires you to run "vagrant up". '
               'And export TEST_ZPLAYS=true')
    @workflow_test(
        _blueprint_path,
        inputs={'hosts_relative_path': source_dict})
    def test_workflow_input_override(self, cfy_local):
        cfy_local.execute('install', task_retries=0)
        self.assertIn(
            'result',
            cfy_local.storage.get_node_instances(
                )[0].runtime_properties.keys())

    @skipUnless(
        environ.get('TEST_ZPLAYS', False),
        reason='This test requires you to run "vagrant up". '
               'And export TEST_ZPLAYS=true')
    @workflow_test(
        _compute_blueprint_path,
        inputs={
            'web_private_key': web_private_key,
            'db_private_key': db_private_key})
    def test_compute_blueprint(self, cfy_local):
        cfy_local.execute('install', task_retries=0)
        self.assertIn(
            'result',
            cfy_local.storage.get_node_instances(
                'ansible_playbook')[0].runtime_properties.keys())
