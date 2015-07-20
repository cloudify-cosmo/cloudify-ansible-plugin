########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
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

# Built-in Imports
import os
import shutil
import tempfile

# Third-party Imports

# Cloudify imports
from cloudify import ctx
from ansible_plugin import utils
from cloudify.decorators import operation


@operation
def configure(user=None, key=None, **kwargs):

    agent_key_path = utils.get_keypair_path(key)
    _, path_to_key = tempfile.mkstemp()
    shutil.copyfile(agent_key_path, path_to_key)
    os.chmod(path_to_key, 0600)

    configuration = '[defaults]\n' \
                    'host_key_checking=False\n' \
                    'private_key_file={0}\n'.format(path_to_key)

    ctx.logger.info('Configuring Anisble.')
    file_path = utils.write_configuration_file(configuration)
    ctx.logger.info('Configured Ansible.')

    os.environ['ANSIBLE_CONFIG'] = file_path
    os.environ['USER'] = utils.get_agent_user(user)
    os.environ['HOME'] = home = os.path.expanduser("~")

    if os.path.exists(os.path.join(home, '.ansible')):
        shutil.rmtree(os.path.join(home, '.ansible'))

    os.makedirs(os.path.join(home, '.ansible'))


@operation
def ansible_playbook(playbooks, inventory=list(), **kwargs):
    """ Runs a playbook as part of a Cloudify lifecycle operation """

    inventory_path = utils.get_inventory_path(inventory)
    ctx.logger.info('Inventory path: {0}.'.format(inventory_path))

    for playbook in playbooks:
        playbook_path = utils.get_playbook_path(playbook)
        ctx.logger.info('Playbook path: {0}.'.format(playbook_path))
        user = utils.get_agent_user()
        executible = utils.get_executible_path('ansible-playbook')
        command = [executible, '--sudo', '-u', user, 
                   '-i', inventory_path, playbook_path,
                   '--timeout=60', '-vvvv']
        ctx.logger.info('Running command: {0}.'.format(command))
        output = utils.run_command(command)
        ctx.logger.info('Command Output: {0}.'.format(output))
        ctx.logger.info('Finished running the Ansible Playbook.')
