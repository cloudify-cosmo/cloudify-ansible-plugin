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

# Third-party Imports

# Cloudify imports
from cloudify import ctx
from ansible_plugin import utils
from cloudify.decorators import operation


@operation
def configure(user, **kwargs):

    configuration = '[defaults]\nhost_key_checking=False ' \
                    'remote_user=ubuntu'

    ctx.logger.info('Configuring Anisble.')

    os.environ["USER"] = user
    os.environ["HOME"] = home = os.path.expanduser("~")

    file_path = utils.write_configuration_file(configuration)

    os.environ['ANSIBLE_CONFIG'] = os.path.dirname(os.path.realpath(file_path))

    if not os.path.exists(os.path.join(home, '.ansible')):
        os.makedirs(os.path.join(home, '.ansible'))

    ctx.logger.info('Configured Ansible.')


@operation
def ansible_playbook(keypair, playbook, private_ip_address, **kwargs):
    """ Runs a playbook as part of a Cloudify lifecycle operation """

    ctx.logger.info('Getting the path to the keypair.')
    path_to_key = utils.get_keypair_path(keypair)
    ctx.logger.info('Got the keypair path: {}'.format(path_to_key))

    ctx.logger.info('Getting the path to the playbook.')
    playbook_path = utils.get_playbook_path(playbook)
    ctx.logger.info('Got the playbook path: {}.'.format(playbook_path))

    ctx.logger.info('Getting the inventory path.')
    inventory_path = utils.get_inventory_path(private_ip_address)
    ctx.logger.info('Got the inventory path: {}.'.format(inventory_path))

    os.chmod(path_to_key, 0600)

    executible = utils.get_executible_path('ansible-playbook')

    command = [executible, '--sudo', '-i', inventory_path,
               playbook_path, '--private-key', path_to_key,
               '--timeout=60', '--forks=1', '-vvvv']

    ctx.logger.info('Running command: {}.'.format(command))

    output = utils.run_command(command)

    ctx.logger.info('Command Output: {}.'.format(output))

    ctx.logger.info('Finished running the Ansible Playbook.')
