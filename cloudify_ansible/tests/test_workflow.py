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
import subprocess
from unittest import skipUnless

from cloudify.workflows import local

from cloudify_ansible_sdk.tests import AnsibleTestBase, mock_sources_dict


IGNORED_LOCAL_WORKFLOW_MODULES = (
    'worker_installer.tasks',
    'plugin_installer.tasks',
    'cloudify_agent.operations',
    'cloudify_agent.installer.operations',
)
PRIVATE_KEY_DIR = '.vagrant/machines/{0}/virtualbox/private_key'

# This just gives us a path to the setup.py directory.
_plugin_directory = \
    '/{0}'.format(
        '/'.join(
            path.abspath(path.dirname(__file__)).split('/')[1:-2]
        )
    )

_blueprint_path = \
   path.join(_plugin_directory,
             'examples/hosts-input-blueprint.yaml')
_compute_blueprint_path = \
   path.join(
       _plugin_directory,
       'examples/compute-blueprint.yaml')
_relationships_blueprint = \
    path.join(_plugin_directory,
              'examples/relationships-blueprint.yaml')
_another_relationships_blueprint = \
    path.join(_plugin_directory,
              'examples/another-relationships-blueprint.yaml')
_openvpn_blueprint = \
    path.join(_plugin_directory,
              'examples/openvpn-blueprint.yaml')
_clearwater_blueprint = \
    path.join(_plugin_directory,
              'examples/clearwater-blueprint.yaml')


def load_new_vagrant_env(boxes=None):
    boxes = boxes or []
    if not boxes:
        subprocess.call("vagrant up",
                        cwd=_plugin_directory,
                        shell=True)
    for box in boxes:
        subprocess.call("vagrant up {0}".format(box),
                        cwd=_plugin_directory,
                        shell=True)


class TestPluginWorkflows(AnsibleTestBase):

    @skipUnless(
        environ.get('TEST_ZPLAYS', False),
        reason='This test requires you to run "vagrant up". '
               'And export TEST_ZPLAYS=true')
    def test1_blueprint_defaults(self):
        load_new_vagrant_env(['web', 'db'])
        cfy_local = local.init_env(
            _blueprint_path,
            'test1_blueprint_defaults',
            ignored_modules=IGNORED_LOCAL_WORKFLOW_MODULES)
        cfy_local.execute('install', task_retries=0)
        self.assertIn(
            'result',
            cfy_local.storage.get_node_instances(
                )[0].runtime_properties.keys())
        subprocess.call("vagrant destroy -f",
                        cwd=_plugin_directory, shell=True)

    @skipUnless(
        environ.get('TEST_ZPLAYS', False),
        reason='This test requires you to run "vagrant up". '
               'And export TEST_ZPLAYS=true')
    def test2_workflow_input_override(self):
        load_new_vagrant_env(['web', 'db'])
        cfy_local = local.init_env(
            _blueprint_path,
            'test2_workflow_input_override',
            inputs={'hosts_relative_path': mock_sources_dict},
            ignored_modules=IGNORED_LOCAL_WORKFLOW_MODULES)
        cfy_local.execute('install', task_retries=0)
        self.assertIn(
            'result',
            cfy_local.storage.get_node_instances(
                )[0].runtime_properties.keys())
        subprocess.call("vagrant destroy -f",
                        cwd=_plugin_directory, shell=True)

    @skipUnless(
        environ.get('TEST_ZPLAYS', False),
        reason='This test requires you to run "vagrant up". '
               'And export TEST_ZPLAYS=true')
    def test3_compute_blueprint(self):
        load_new_vagrant_env(['web', 'db'])
        with open(PRIVATE_KEY_DIR.format('web'), 'r') as infile:
            web_private_key = infile.read()
        with open(PRIVATE_KEY_DIR.format('db'), 'r') as infile:
            db_private_key = infile.read()
        cfy_local = local.init_env(
            _compute_blueprint_path,
            'test3_compute_blueprint',
            inputs={
                'web_private_key': web_private_key,
                'db_private_key': db_private_key
            },
            ignored_modules=IGNORED_LOCAL_WORKFLOW_MODULES)
        cfy_local.execute('install', task_retries=0)
        self.assertIn(
            'result',
            cfy_local.storage.get_node_instances(
                'ansible_playbook')[0].runtime_properties.keys())
        subprocess.call("vagrant destroy -f",
                        cwd=_plugin_directory, shell=True)

    @skipUnless(
        environ.get('TEST_ZPLAYS', False),
        reason='This test requires you to run "vagrant up". '
               'And export TEST_ZPLAYS=true')
    def test4_relationships_blueprint(self):
        load_new_vagrant_env(['web', 'db'])
        with open(PRIVATE_KEY_DIR.format('web'), 'r') as infile:
            web_private_key = infile.read()
        with open(PRIVATE_KEY_DIR.format('db'), 'r') as infile:
            db_private_key = infile.read()
        cfy_local = local.init_env(
            _relationships_blueprint,
            'test1_blueprint_defaults',
            inputs={
                'web_private_key': web_private_key,
                'db_private_key': db_private_key
            },
            ignored_modules=IGNORED_LOCAL_WORKFLOW_MODULES)
        cfy_local.execute('install', task_retries=0)
        self.assertIn(
            'result',
            cfy_local.storage.get_node_instances(
                'ansible_playbook')[0].runtime_properties.keys())
        subprocess.call("vagrant destroy -f",
                        cwd=_plugin_directory, shell=True)

    @skipUnless(
        environ.get('TEST_ZPLAYS', False),
        reason='This test requires you to run "vagrant up". '
               'And export TEST_ZPLAYS=true')
    def test5_another_relationships_blueprint(self):
        load_new_vagrant_env(['web', 'db'])
        with open(PRIVATE_KEY_DIR.format('web'), 'r') as infile:
            web_private_key = infile.read()
        with open(PRIVATE_KEY_DIR.format('db'), 'r') as infile:
            db_private_key = infile.read()
        cfy_local = local.init_env(
            _another_relationships_blueprint,
            'test5_another_relationships_blueprint',
            inputs={
                'web_private_key': web_private_key,
                'db_private_key': db_private_key
            },
            ignored_modules=IGNORED_LOCAL_WORKFLOW_MODULES)
        cfy_local.execute('install', task_retries=0)
        self.assertIn(
            'result',
            cfy_local.storage.get_node_instances(
                'ansible_playbook')[0].runtime_properties.keys())
        subprocess.call("vagrant destroy -f",
                        cwd=_plugin_directory, shell=True)

    @skipUnless(
        environ.get('TEST_OPENVPN', False),
        reason='This test requires you to run "vagrant up". '
               'And export TEST_OPENVPN=true')
    def test6_openvpn_blueprint(self):
        load_new_vagrant_env(['vpn'])
        with open(PRIVATE_KEY_DIR.format('vpn'), 'r') as infile:
            vpn_private_key = infile.read()
        cfy_local = local.init_env(
            _openvpn_blueprint,
            'test6_openvpn_blueprint',
            inputs={'openvpn_private_key': vpn_private_key},
            ignored_modules=IGNORED_LOCAL_WORKFLOW_MODULES)
        cfy_local.execute('install', task_retries=0)
        self.assertIn(
            'result',
            cfy_local.storage.get_node_instances(
                'openvpn')[0].runtime_properties.keys())
        subprocess.call("vagrant destroy -f",
                        cwd=_plugin_directory, shell=True)

    @skipUnless(
        environ.get('TEST_ZPLAYS', False),
        reason='This test requires you to run "vagrant up". '
               'And export TEST_ZPLAYS=true')
    def test6_clearwater_blueprint(self):
        load_new_vagrant_env(['ellis',
                              'bono',
                              'sprout',
                              'homer',
                              'homestead',
                              'ralf',
                              'bind'])
        with open(PRIVATE_KEY_DIR.format('ellis'), 'r') as infile:
            ellis_private_key = infile.read()
        with open(PRIVATE_KEY_DIR.format('bono'), 'r') as infile:
            bono_private_key = infile.read()
        with open(PRIVATE_KEY_DIR.format('sprout'), 'r') as infile:
            sprout_private_key = infile.read()
        with open(PRIVATE_KEY_DIR.format('homer'), 'r') as infile:
            homer_private_key = infile.read()
        with open(PRIVATE_KEY_DIR.format('homestead'), 'r') as infile:
            homestead_private_key = infile.read()
        with open(PRIVATE_KEY_DIR.format('ralf'), 'r') as infile:
            ralf_private_key = infile.read()
        with open(PRIVATE_KEY_DIR.format('bind'), 'r') as infile:
            bind_private_key = infile.read()
        cfy_local = local.init_env(
            _clearwater_blueprint,
            'test6_clearwater_blueprint',
            inputs={
                'ellis_private_key': ellis_private_key,
                'bono_private_key': bono_private_key,
                'sprout_private_key': sprout_private_key,
                'homer_private_key': homer_private_key,
                'homestead_private_key': homestead_private_key,
                'ralf_private_key': ralf_private_key,
                'bind_private_key': bind_private_key,
            },
            ignored_modules=IGNORED_LOCAL_WORKFLOW_MODULES)
        cfy_local.execute('install', task_retries=0)
        self.assertIn(
            'result',
            cfy_local.storage.get_node_instances(
                'ellis')[0].runtime_properties.keys())
        self.assertIn(
            'result',
            cfy_local.storage.get_node_instances(
                'bono')[0].runtime_properties.keys())
        self.assertIn(
            'result',
            cfy_local.storage.get_node_instances(
                'sprout')[0].runtime_properties.keys())
        self.assertIn(
            'result',
            cfy_local.storage.get_node_instances(
                'homer')[0].runtime_properties.keys())
        self.assertIn(
            'result',
            cfy_local.storage.get_node_instances(
                'homestead')[0].runtime_properties.keys())
        self.assertIn(
            'result',
            cfy_local.storage.get_node_instances(
                'ralf')[0].runtime_properties.keys())
        self.assertIn(
            'result',
            cfy_local.storage.get_node_instances(
                'bind')[0].runtime_properties.keys())
        subprocess.call("vagrant destroy -f",
                        cwd=_plugin_directory, shell=True)
