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

from cloudify.test_utils import workflow_test

from cloudify_ansible_sdk.tests import AnsibleTestBase, mock_sources_dict


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
        subprocess.call("vagrant destroy -f",
                        cwd=_plugin_directory, shell=True)
        subprocess.call("vagrant up",
                        cwd=_plugin_directory, shell=True)
    for box in boxes:
        subprocess.call("vagrant destroy -f {0}".format(box),
                        cwd=_plugin_directory, shell=True)
        subprocess.call("vagrant up {0}".format(box),
                        cwd=_plugin_directory, shell=True)


load_new_vagrant_env()

web_private_key_path = \
    '.vagrant/machines/{0}/virtualbox/private_key'.format('web')
db_private_key_path = \
    '.vagrant/machines/{0}/virtualbox/private_key'.format('db')
openvpn_private_key_path = \
    '.vagrant/machines/{0}/virtualbox/private_key'.format('vpn')
ellis_private_key_path = \
    '.vagrant/machines/{0}/virtualbox/private_key'.format('ellis')
bono_private_key_path = \
    '.vagrant/machines/{0}/virtualbox/private_key'.format('bono')
sprout_private_key_path = \
    '.vagrant/machines/{0}/virtualbox/private_key'.format('sprout')
homer_private_key_path = \
    '.vagrant/machines/{0}/virtualbox/private_key'.format('homer')
homestead_private_key_path = \
    '.vagrant/machines/{0}/virtualbox/private_key'.format('homestead')
ralf_private_key_path = \
    '.vagrant/machines/{0}/virtualbox/private_key'.format('ralf')
bind_private_key_path = \
    '.vagrant/machines/{0}/virtualbox/private_key'.format('bind')

if environ.get('TEST_ZPLAYS', False):
    with open(web_private_key_path, 'r') as infile:
        web_private_key = infile.read()
    with open(db_private_key_path, 'r') as infile:
        db_private_key = infile.read()
    with open(openvpn_private_key_path, 'r') as infile:
        openvpn_private_key = infile.read()
    with open(ellis_private_key_path, 'r') as infile:
        ellis_private_key = infile.read()
    with open(bono_private_key_path, 'r') as infile:
        bono_private_key = infile.read()
    with open(sprout_private_key_path, 'r') as infile:
        sprout_private_key = infile.read()
    with open(homer_private_key_path, 'r') as infile:
        homer_private_key = infile.read()
    with open(homestead_private_key_path, 'r') as infile:
        homestead_private_key = infile.read()
    with open(ralf_private_key_path, 'r') as infile:
        ralf_private_key = infile.read()
    with open(bind_private_key_path, 'r') as infile:
        bind_private_key = infile.read()
else:
    web_private_key = None
    db_private_key = None
    openvpn_private_key = None
    ellis_private_key = None
    bono_private_key = None
    sprout_private_key = None
    homer_private_key = None
    homestead_private_key = None
    ralf_private_key = None
    bind_private_key = None


class TestPluginWorkflows(AnsibleTestBase):

    @skipUnless(
        environ.get('TEST_ZPLAYS', False),
        reason='This test requires you to run "vagrant up". '
               'And export TEST_ZPLAYS=true')
    @workflow_test(_blueprint_path)
    def test1_blueprint_defaults(self, cfy_local):
        cfy_local.execute('install', task_retries=0)
        self.assertIn(
            'result',
            cfy_local.storage.get_node_instances(
                )[0].runtime_properties.keys())
        load_new_vagrant_env(['db', 'web'])

    @skipUnless(
        environ.get('TEST_ZPLAYS', False),
        reason='This test requires you to run "vagrant up". '
               'And export TEST_ZPLAYS=true')
    @workflow_test(
        _blueprint_path,
        inputs={'hosts_relative_path': mock_sources_dict})
    def test2_workflow_input_override(self, cfy_local):
        load_new_vagrant_env(['db', 'web'])
        cfy_local.execute('install', task_retries=0)
        self.assertIn(
            'result',
            cfy_local.storage.get_node_instances(
                )[0].runtime_properties.keys())
        load_new_vagrant_env(['db', 'web'])

    @skipUnless(
        environ.get('TEST_ZPLAYS', False),
        reason='This test requires you to run "vagrant up". '
               'And export TEST_ZPLAYS=true')
    @workflow_test(
        _compute_blueprint_path,
        inputs={
            'web_private_key': web_private_key,
            'db_private_key': db_private_key})
    def test3_compute_blueprint(self, cfy_local):
        load_new_vagrant_env(['db', 'web'])
        cfy_local.execute('install', task_retries=0)
        self.assertIn(
            'result',
            cfy_local.storage.get_node_instances(
                'ansible_playbook')[0].runtime_properties.keys())
        load_new_vagrant_env(['db', 'web'])

    @skipUnless(
        environ.get('TEST_ZPLAYS', False),
        reason='This test requires you to run "vagrant up". '
               'And export TEST_ZPLAYS=true')
    @workflow_test(
        _relationships_blueprint,
        inputs={
            'web_private_key': web_private_key,
            'db_private_key': db_private_key})
    def test4_relationships_blueprint(self, cfy_local):
        load_new_vagrant_env(['db', 'web'])
        cfy_local.execute('install', task_retries=0)
        self.assertIn(
            'result',
            cfy_local.storage.get_node_instances(
                'ansible_playbook')[0].runtime_properties.keys())
        load_new_vagrant_env(['db', 'web'])

    @skipUnless(
        environ.get('TEST_ZPLAYS', False),
        reason='This test requires you to run "vagrant up". '
               'And export TEST_ZPLAYS=true')
    @workflow_test(
        _another_relationships_blueprint,
        inputs={
            'web_private_key': web_private_key,
            'db_private_key': db_private_key})
    def test5_another_relationships_blueprint(self, cfy_local):
        load_new_vagrant_env(['db', 'web'])
        cfy_local.execute('install', task_retries=0)
        self.assertIn(
            'result',
            cfy_local.storage.get_node_instances(
                'ansible_playbook')[0].runtime_properties.keys())
        load_new_vagrant_env(['db', 'web'])

    @skipUnless(
        environ.get('TEST_OPENVPN', False),
        reason='This test requires you to run "vagrant up". '
               'And export TEST_OPENVPN=true')
    @workflow_test(
        _openvpn_blueprint,
        inputs={
            'openvpn_private_key': openvpn_private_key})
    def test6_openvpn_blueprint(self, cfy_local):
        cfy_local.execute('install', task_retries=0)
        self.assertIn(
            'result',
            cfy_local.storage.get_node_instances(
                'openvpn')[0].runtime_properties.keys())

    @skipUnless(
        environ.get('TEST_ZPLAYS', False),
        reason='This test requires you to run "vagrant up". '
               'And export TEST_ZPLAYS=true')
    @workflow_test(
        _clearwater_blueprint,
        inputs={
            'ellis_private_key': ellis_private_key,
            'bono_private_key': bono_private_key,
            'sprout_private_key': sprout_private_key,
            'homer_private_key': homer_private_key,
            'homestead_private_key': homestead_private_key,
            'ralf_private_key': ralf_private_key,
            'bind_private_key': bind_private_key,
        })
    def test6_clearwater_blueprint(self, cfy_local):
        load_new_vagrant_env(['db', 'web'])
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
