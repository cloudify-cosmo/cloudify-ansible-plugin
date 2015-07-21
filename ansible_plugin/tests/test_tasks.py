########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.


import os
import testtools
import subprocess

from cloudify.workflows import local


IGNORE = (
    'worker_installer.tasks',
    'plugin_installer.tasks'
)

BLUEPRINTS = [
    'blueprint.yaml'
]


class TestAnsiblePlugin(testtools.TestCase):

    def _run_shell(self, cmd):
        p = subprocess.Popen(cmd, shell=True)
        out, err = p.communicate()
        return out

    def _init_env(self, bp_path, inputs):

        return local.init_env(bp_path,
                              name=self._testMethodName,
                              inputs=inputs,
                              ignored_modules=IGNORE)

    def _exec_env(self, workflow_name, parameters):

        return self.env.execute(workflow_name,
                                parameters=parameters,
                                task_retries=0)

    def _get_blueprint_path(self, blueprint):

        return os.path.join(os.path.dirname(__file__),
                            'blueprint', blueprint)

    def _user(self, user=None):

        if not user:
            user = os.getlogin()
        return user

    def _key(self, user, key=None):

        if not key:
            key = os.path.expanduser('~/.ssh/agent_key.pem')
        return key

    def _run(self, user=None, key=None,
             blueprint='local.yaml',
             workflow_name='install',
             properties=None):

        user = user if user else self._user()
        key = key if key else self._key(user)

        inputs = {
            'agent_user': user,
            'key_file': key,
            'host_ip': '127.0.0.1'
        }

        blueprint_path = self._get_blueprint_path(blueprint)
        self.env = self._init_env(blueprint_path, inputs)
        result = self._exec_env(workflow_name, properties)

        if not result:
            node_instances = \
                self.env.storage.get_node_instances()
            result = node_instances[0]['runtime_properties']

        return result

    def test_install_clean(self):

        def stop_apache(self):
            self._run_shell('sudo service apache stop')

        def uninstall_apache(self):
            self._run_shell('sudo apt-get remove -y apache2')
        self.addCleanup(uninstall_apache)
        self.addCleanup(stop_apache)
        self._run()
