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
import tempfile
import testtools
import subproccess
from Crypto.PublicKey import RSA

from cloudify.workflows import local


IGNORED_LOCAL_WORKFLOW_MODULES = (
    'worker_installer.tasks',
    'plugin_installer.tasks'
)

BLUEPRINTS = [
    'blueprint.yaml'
]


class TestAnsiblePlugin(testtools.TestCase):

    def _user(self, user=None):
        if not user:
            return os.getlogin()

    def _key(self, key=None):
        if not key:
            rsa_material = RSA.generate(2048)
            _, key = tempfile.mkstemp()
            pubkey = rsa_material.publickey()
            with open(key, 'w') as f:
                f.write(pubkey.exportKey('OpenSSH'))
        return key

    def _run(self, blueprint='local.yaml',
                   playbook='playbook.yaml',
                   user, key,
                   workflow_name='install'):

        inputs = {
            'playbook_file': playbook,
            'agent_user': user,
            'key_file': key
        }

        blueprint_path = os.path.join(os.path.dirname(__file__),
                                      'blueprint', blueprint)

        self.env = local.init_env(blueprint_path,
                                  name=self._testMethodName,
                                  inputs=inputs)

        result = self.env.execute(workflow_name,
                                  parameters=parameters,
                                  task_retries=0)

        if not result:
            result = self.env.storage.get_node_instances()[0][
                'runtime_properties']

        return result
